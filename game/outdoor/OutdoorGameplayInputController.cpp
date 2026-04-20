#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"
#include "game/ui/HudUiService.h"
#include "game/ui/KeyboardScreenLayout.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;
constexpr uint64_t SaveGameDoubleClickWindowMs = 500;
constexpr int DwiMapId = 1;
constexpr uint16_t DwiMeteorShowerEventId = 456;
constexpr size_t SaveLoadVisibleSlotCount = 10;

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
    else
    {
        pressedTarget = noneTarget;
    }
}

std::optional<SDL_Scancode> firstNewlyPressedScancode(
    const bool *pKeyboardState,
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousState)
{
    if (pKeyboardState == nullptr)
    {
        return std::nullopt;
    }

    for (int scancode = SDL_SCANCODE_UNKNOWN + 1; scancode < SDL_SCANCODE_COUNT; ++scancode)
    {
        if (pKeyboardState[scancode] && previousState[scancode] == 0)
        {
            return static_cast<SDL_Scancode>(scancode);
        }
    }

    return std::nullopt;
}

const char *activeGameplayButtonLayoutId(const OutdoorGameView &view, const char *pWideId, const char *pStandardId)
{
    return view.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard ? pStandardId : pWideId;
}
} // namespace

void OutdoorGameplayInputController::updateCameraFromInput(
    OutdoorGameView &view,
    float mouseWheelDelta,
    float deltaSeconds)
{
    const float displayDeltaSeconds = std::max(deltaSeconds, 0.000001f);
    const float instantaneousFramesPerSecond = 1.0f / displayDeltaSeconds;
    view.m_framesPerSecond = (view.m_framesPerSecond == 0.0f)
        ? instantaneousFramesPerSecond
        : (view.m_framesPerSecond * 0.9f + instantaneousFramesPerSecond * 0.1f);
    deltaSeconds = std::min(deltaSeconds, 0.05f);

    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);

    if (pKeyboardState == nullptr)
    {
        return;
    }

    const auto updatePreviousKeyboardState =
        [&view, pKeyboardState]()
        {
            for (int scancode = 0; scancode < SDL_SCANCODE_COUNT; ++scancode)
            {
                view.previousKeyboardState()[scancode] = pKeyboardState[scancode] ? 1 : 0;
            }
        };

    struct PreviousKeyboardStateUpdater
    {
        const std::function<void()> &updater;

        ~PreviousKeyboardStateUpdater()
        {
            updater();
        }
    };

    const PreviousKeyboardStateUpdater previousKeyboardStateUpdater = {updatePreviousKeyboardState};
    const auto isActionPressed =
        [&view, pKeyboardState](KeyboardAction action) -> bool
        {
            return view.m_gameSettings.keyboard.isPressed(action, pKeyboardState);
        };
    const auto isActionNewlyPressed =
        [&view, pKeyboardState](KeyboardAction action) -> bool
        {
            const SDL_Scancode scancode = view.m_gameSettings.keyboard.binding(action);

            return pKeyboardState != nullptr
                && scancode > SDL_SCANCODE_UNKNOWN
                && scancode < SDL_SCANCODE_COUNT
                && pKeyboardState[scancode]
                && view.previousKeyboardState()[scancode] == 0;
        };

    const bool hasActiveLootView =
        view.m_pOutdoorWorldRuntime != nullptr
        && (view.m_pOutdoorWorldRuntime->activeChestView() != nullptr
            || view.m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isEventDialogActive = view.hasActiveEventDialog();
    const bool hasPendingSpellCast = view.m_pendingSpellCast.active;
    const bool isSpellbookActive = view.m_spellbook.active;
    const bool isRestScreenActive = view.m_restScreen.active;
    const bool isMenuActive = view.m_menuScreen.active;
    const bool isControlsActive = view.m_controlsScreen.active;
    const bool isKeyboardActive = view.m_keyboardScreen.active;
    const bool isSaveGameActive = view.m_saveGameScreen.active;
    const bool isLoadGameActive = view.m_loadGameScreen.active;
    const bool isJournalActive = view.m_journalScreen.active;
    const bool isUtilitySpellModalActive =
        view.m_utilitySpellOverlay.active
        && view.m_utilitySpellOverlay.mode != OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget;
    const bool blocksUnderlyingMouseInput =
        view.currentHudScreenState() != OutdoorGameView::HudScreenState::Gameplay
        || view.m_readableScrollOverlay.active;
    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    int screenWidth = 0;
    int screenHeight = 0;

    if (pWindow != nullptr)
    {
        SDL_GetWindowSizeInPixels(pWindow, &screenWidth, &screenHeight);
    }

    float gameplayMouseX = 0.0f;
    float gameplayMouseY = 0.0f;
    const SDL_MouseButtonFlags gameplayMouseButtons = SDL_GetMouseState(&gameplayMouseX, &gameplayMouseY);
    const bool isRightMousePressed = (gameplayMouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool gameplayMouseLookAllowed = view.shouldEnableGameplayMouseLook();
    const bool gameplayCursorModeActive = gameplayMouseLookAllowed && isRightMousePressed;
    const bool gameplayMouseLookActive = gameplayMouseLookAllowed && !gameplayCursorModeActive;
    const bool allowGameplayPointerInput = !gameplayMouseLookAllowed || gameplayCursorModeActive;

    view.m_gameplayCursorModeActive = gameplayCursorModeActive;
    view.m_gameplayMouseLookActive = gameplayMouseLookActive;
    view.syncGameplayMouseLookMode(pWindow, gameplayMouseLookActive);

    if (view.m_pOutdoorPartyRuntime != nullptr
        && screenWidth > 0
        && screenHeight > 0
        && allowGameplayPointerInput
        && !isSpellbookActive
        && !isRestScreenActive
        && !isMenuActive
        && !isControlsActive
        && !isKeyboardActive
        && !isSaveGameActive
        && !isLoadGameActive
        && !isJournalActive
        && !isUtilitySpellModalActive
        && !view.m_readableScrollOverlay.active)
    {
        float portraitMouseX = 0.0f;
        float portraitMouseY = 0.0f;
        const SDL_MouseButtonFlags portraitMouseButtons = SDL_GetMouseState(&portraitMouseX, &portraitMouseY);
        const HudPointerState portraitPointerState = {
            portraitMouseX,
            portraitMouseY,
            (portraitMouseButtons & SDL_BUTTON_LMASK) != 0
        };
        const bool requireGameplayReady =
            !isEventDialogActive
            && !view.m_characterScreenOpen
            && !hasActiveLootView
            && !isSpellbookActive
            && !isRestScreenActive
            && !isMenuActive
            && !isControlsActive
            && !isSaveGameActive
            && !isLoadGameActive
            && !isJournalActive;

        handlePointerClickRelease(
            portraitPointerState,
            view.m_partyPortraitClickLatch,
            view.m_partyPortraitPressedIndex,
            std::optional<size_t>{},
            [&view, screenWidth, screenHeight](float x, float y) -> std::optional<size_t>
            {
                return view.resolvePartyPortraitIndexAtPoint(screenWidth, screenHeight, x, y);
            },
            [&view, requireGameplayReady, hasActiveLootView, hasPendingSpellCast](const std::optional<size_t> &memberIndex)
            {
                if (memberIndex)
                {
                    if (hasPendingSpellCast)
                    {
                        view.tryResolvePendingSpellCast({}, memberIndex);
                        return;
                    }

                    if (view.m_heldInventoryItem.active)
                    {
                        const bool switchCharacterOnFailedPlacement =
                            view.m_characterScreenOpen && view.m_characterPage == OutdoorGameView::CharacterPage::Inventory;

                        if (view.tryAutoPlaceHeldItemOnPartyMember(*memberIndex, !switchCharacterOnFailedPlacement))
                        {
                            view.m_lastPartyPortraitClickedIndex = std::nullopt;
                        }
                        else if (switchCharacterOnFailedPlacement)
                        {
                            view.trySelectPartyMember(*memberIndex, requireGameplayReady);
                        }

                        return;
                    }

                    const uint64_t nowTicks = SDL_GetTicks();
                    const bool isGameplayInventoryDoubleClick =
                        requireGameplayReady
                        && view.m_lastPartyPortraitClickedIndex.has_value()
                        && *view.m_lastPartyPortraitClickedIndex == *memberIndex
                        && nowTicks >= view.m_lastPartyPortraitClickTicks
                        && nowTicks - view.m_lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;
                    const bool isChestInventoryDoubleClick =
                        hasActiveLootView
                        && view.m_lastPartyPortraitClickedIndex.has_value()
                        && *view.m_lastPartyPortraitClickedIndex == *memberIndex
                        && nowTicks >= view.m_lastPartyPortraitClickTicks
                        && nowTicks - view.m_lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;

                    if (view.trySelectPartyMember(*memberIndex, requireGameplayReady))
                    {
                        if (isGameplayInventoryDoubleClick)
                        {
                            view.m_characterScreenOpen = true;
                            view.m_adventurersInnRosterOverlayOpen = false;
                            view.m_characterScreenSource = OutdoorGameView::CharacterScreenSource::Party;
                            view.m_characterScreenSourceIndex = 0;
                            view.m_adventurersInnScrollOffset = 0;
                            view.m_characterPage = OutdoorGameView::CharacterPage::Inventory;
                            view.m_characterDollJewelryOverlayOpen = false;
                        }
                        else if (isChestInventoryDoubleClick)
                        {
                            view.openInventoryNestedOverlay(OutdoorGameView::InventoryNestedOverlayMode::ChestTransfer);
                        }

                        view.m_lastPartyPortraitClickTicks = nowTicks;
                        view.m_lastPartyPortraitClickedIndex = *memberIndex;
                    }
                }
            });
    }
    else
    {
        view.m_partyPortraitClickLatch = false;
        view.m_partyPortraitPressedIndex = std::nullopt;
    }

    const bool canToggleSpellbook =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_restScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    const bool canToggleMenu =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_restScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    if (!isMenuActive && !isControlsActive && !isKeyboardActive && !isSaveGameActive && !isLoadGameActive
        && pKeyboardState[SDL_SCANCODE_ESCAPE])
    {
        if (!view.interactionState().menuToggleLatch)
        {
            if (canToggleMenu)
            {
                view.openMenu();
            }

            view.interactionState().menuToggleLatch = true;
        }
    }
    else if (!isMenuActive && !isControlsActive && !isKeyboardActive && !isSaveGameActive && !isLoadGameActive)
    {
        view.interactionState().menuToggleLatch = false;
    }

    if (canToggleMenu && allowGameplayPointerInput && !blocksUnderlyingMouseInput && screenWidth > 0 && screenHeight > 0)
    {
        const char *pOptionsButtonLayoutId =
            activeGameplayButtonLayoutId(view, "OutdoorButtonOptions", "OutdoorStandardButtonOptions");
        float optionsButtonMouseX = 0.0f;
        float optionsButtonMouseY = 0.0f;
        const SDL_MouseButtonFlags optionsButtonMouseButtons =
            SDL_GetMouseState(&optionsButtonMouseX, &optionsButtonMouseY);
        const HudPointerState optionsButtonPointerState = {
            optionsButtonMouseX,
            optionsButtonMouseY,
            (optionsButtonMouseButtons & SDL_BUTTON_LMASK) != 0
        };

        handlePointerClickRelease(
            optionsButtonPointerState,
            view.m_optionsButtonClickLatch,
            view.m_optionsButtonPressed,
            false,
            [&view, pOptionsButtonLayoutId, screenWidth, screenHeight](float pointerX, float pointerY) -> bool
            {
                const OutdoorGameView::HudLayoutElement *pLayout =
                    HudUiService::findHudLayoutElement(view, pOptionsButtonLayoutId);

                if (pLayout == nullptr)
                {
                    return false;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        pOptionsButtonLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                return resolved
                    && HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY);
            },
            [&view](bool target)
            {
                if (target)
                {
                    view.openMenu();
                }
            });
    }
    else if (!view.m_menuScreen.active && !view.m_controlsScreen.active && !view.m_keyboardScreen.active)
    {
        view.m_optionsButtonClickLatch = false;
        view.m_optionsButtonPressed = false;
    }

    const bool canOpenRestScreen =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    if (canOpenRestScreen && isActionPressed(KeyboardAction::Rest))
    {
        if (!view.m_restToggleLatch)
        {
            view.openRestScreen();
            view.m_restToggleLatch = true;
        }
    }
    else
    {
        view.m_restToggleLatch = false;
    }

    if (canOpenRestScreen && allowGameplayPointerInput && !blocksUnderlyingMouseInput && screenWidth > 0 && screenHeight > 0)
    {
        const char *pRestButtonLayoutId =
            activeGameplayButtonLayoutId(view, "OutdoorButtonRest", "OutdoorStandardButtonRest");
        float restButtonMouseX = 0.0f;
        float restButtonMouseY = 0.0f;
        const SDL_MouseButtonFlags restButtonMouseButtons =
            SDL_GetMouseState(&restButtonMouseX, &restButtonMouseY);
        const HudPointerState restButtonPointerState = {
            restButtonMouseX,
            restButtonMouseY,
            (restButtonMouseButtons & SDL_BUTTON_LMASK) != 0
        };
        const OutdoorGameView::RestPointerTarget noneRestTarget = {};

        handlePointerClickRelease(
            restButtonPointerState,
            view.interactionState().restClickLatch,
            view.interactionState().restPressedTarget,
            noneRestTarget,
            [&view, pRestButtonLayoutId, screenWidth, screenHeight](float pointerX, float pointerY)
                -> OutdoorGameView::RestPointerTarget
            {
                const OutdoorGameView::HudLayoutElement *pLayout =
                    HudUiService::findHudLayoutElement(view, pRestButtonLayoutId);

                if (pLayout == nullptr)
                {
                    return {};
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        pRestButtonLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {};
                }

                return {OutdoorGameView::RestPointerTargetType::OpenButton};
            },
            [&view](const OutdoorGameView::RestPointerTarget &target)
            {
                if (target.type == OutdoorGameView::RestPointerTargetType::OpenButton)
                {
                    view.openRestScreen();
                }
            });
    }
    else if (!view.m_restScreen.active)
    {
        view.interactionState().restClickLatch = false;
        view.interactionState().restPressedTarget = {};
    }

    const bool canToggleAdventurersInn =
        !isEventDialogActive
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    const bool canToggleJournal =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_restScreen.active
        && !view.m_heldInventoryItem.active;

    if (canToggleJournal && allowGameplayPointerInput && !blocksUnderlyingMouseInput && screenWidth > 0 && screenHeight > 0)
    {
        const char *pBooksButtonLayoutId =
            activeGameplayButtonLayoutId(view, "OutdoorButtonBooks", "OutdoorStandardButtonBooks");
        float booksButtonMouseX = 0.0f;
        float booksButtonMouseY = 0.0f;
        const SDL_MouseButtonFlags booksButtonMouseButtons =
            SDL_GetMouseState(&booksButtonMouseX, &booksButtonMouseY);
        const HudPointerState booksButtonPointerState = {
            booksButtonMouseX,
            booksButtonMouseY,
            (booksButtonMouseButtons & SDL_BUTTON_LMASK) != 0
        };

        handlePointerClickRelease(
            booksButtonPointerState,
            view.m_booksButtonClickLatch,
            view.m_booksButtonPressed,
            false,
            [&view, pBooksButtonLayoutId, screenWidth, screenHeight](float pointerX, float pointerY) -> bool
            {
                const OutdoorGameView::HudLayoutElement *pLayout =
                    HudUiService::findHudLayoutElement(view, pBooksButtonLayoutId);

                if (pLayout == nullptr)
                {
                    return false;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        pBooksButtonLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                return resolved
                    && HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY);
            },
            [&view](bool target)
            {
                if (target)
                {
                    view.openJournal();
                }
            });
    }
    else if (!view.m_journalScreen.active)
    {
        view.m_booksButtonClickLatch = false;
        view.m_booksButtonPressed = false;
    }

    GameplayOverlayContext overlayContext = view.createGameplayOverlayContext();
    const bool isResidentSelectionMode =
        isEventDialogActive
        && !view.m_activeEventDialog.actions.empty()
        && std::all_of(
            view.m_activeEventDialog.actions.begin(),
            view.m_activeEventDialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
    const GameplayUiOverlayInputResult overlayInputResult =
        GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
            overlayContext,
            pKeyboardState,
            screenWidth,
            screenHeight,
            GameplayUiOverlayInputConfig{
                .hasActiveLootView = hasActiveLootView,
                .canToggleJournal = canToggleJournal,
                .mapShortcutPressed = pKeyboardState[SDL_SCANCODE_M] || isActionPressed(KeyboardAction::MapBook),
                .storyShortcutPressed = isActionPressed(KeyboardAction::History),
                .notesShortcutPressed = isActionPressed(KeyboardAction::AutoNotes),
                .zoomInPressed = isActionPressed(KeyboardAction::ZoomIn),
                .zoomOutPressed = isActionPressed(KeyboardAction::ZoomOut),
                .mouseWheelDelta = mouseWheelDelta,
                .activeEventDialog = isEventDialogActive,
                .residentSelectionMode = isResidentSelectionMode,
                .restActive = view.m_restScreen.active,
                .menuActive = view.m_menuScreen.active,
                .controlsActive = view.m_controlsScreen.active,
                .keyboardActive = view.m_keyboardScreen.active,
                .videoOptionsActive = view.m_videoOptionsScreen.active,
                .saveGameActive = view.m_saveGameScreen.active,
                .spellbookActive = view.m_spellbook.active,
                .characterScreenOpen = view.m_characterScreenOpen,
            },
            GameplayUiOverlayInputCallbacks{
                .resetDialogueInteractionState =
                    [&view]()
                    {
                        view.interactionState().eventDialogSelectUpLatch = false;
                        view.interactionState().eventDialogSelectDownLatch = false;
                        view.interactionState().eventDialogAcceptLatch = false;
                        view.interactionState().eventDialogPartySelectLatches.fill(false);
                        view.interactionState().dialogueClickLatch = false;
                        view.interactionState().dialoguePressedTarget = {};
                    },
                .handleSpellbookOverlayInput =
                    [&overlayContext](const bool *pState, int width, int height)
                    {
                        GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
                            overlayContext,
                            pState,
                            width,
                            height);
                    },
                .handleCharacterOverlayInput =
                    [&view](const bool *pState, int width, int height)
                    {
                        GameplayPartyOverlayInputController::handleCharacterOverlayInput(
                            view,
                            pState,
                            width,
                            height);
                    }});

    if (overlayInputResult.journalInputConsumed)
    {
        return;
    }

    if (canToggleAdventurersInn && pKeyboardState[SDL_SCANCODE_P])
    {
        if (!view.m_adventurersInnToggleLatch)
        {
            if (overlayContext.isAdventurersInnCharacterSourceActive())
            {
                view.m_characterScreenOpen = false;
                view.m_characterDollJewelryOverlayOpen = false;
                view.m_adventurersInnRosterOverlayOpen = false;
            }
            else if (view.m_pOutdoorPartyRuntime != nullptr
                && !view.m_pOutdoorPartyRuntime->party().adventurersInnMembers().empty())
            {
                view.m_characterScreenOpen = true;
                view.m_adventurersInnRosterOverlayOpen = true;
                view.m_characterScreenSource = OutdoorGameView::CharacterScreenSource::AdventurersInn;
                view.m_characterScreenSourceIndex = 0;
                view.m_adventurersInnScrollOffset = 0;
                view.m_characterPage = OutdoorGameView::CharacterPage::Inventory;
                view.m_characterDollJewelryOverlayOpen = false;
            }
            else
            {
                view.setStatusBarEvent("The Adventurer's Inn is empty.");
            }

            view.m_adventurersInnToggleLatch = true;
        }
    }
    else
    {
        view.m_adventurersInnToggleLatch = false;
    }

    const bool canToggleInventory =
        !isEventDialogActive
        && !view.m_restScreen.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_journalScreen.active;

    const bool canCyclePartyMember =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active;

    GameplayScreenHotkeyController::handleGameplayScreenHotkeys(
        overlayContext,
        pKeyboardState,
        GameplayScreenHotkeyConfig{
            .canToggleSpellbook = canToggleSpellbook,
            .canToggleInventory = canToggleInventory,
            .canCyclePartyMember = canCyclePartyMember,
            .hasActiveLootView = hasActiveLootView,
            .requireGameplayReadyForPartySelection = true,
        });

    if (canCyclePartyMember)
    {
        if (isActionPressed(KeyboardAction::AlwaysRun))
        {
            if (!view.m_toggleRunningLatch)
            {
                view.m_gameSettings.alwaysRun = !view.m_gameSettings.alwaysRun;

                if (view.m_pOutdoorPartyRuntime != nullptr)
                {
                    view.m_pOutdoorPartyRuntime->setRunning(view.m_gameSettings.alwaysRun);
                }

                view.commitSettingsChange();
                view.m_toggleRunningLatch = true;
            }
        }
        else
        {
            view.m_toggleRunningLatch = false;
        }
    }
    else
    {
        view.m_toggleRunningLatch = false;
    }

    if (!isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_menuScreen.active
        && !view.m_controlsScreen.active
        && !view.m_keyboardScreen.active
        && !view.m_saveGameScreen.active
        && !view.m_loadGameScreen.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active)
    {
        const bool isQuickCastPressed = isActionPressed(KeyboardAction::CastReady);
        bool quickCastReadyMemberTransitionWhileHeld = false;

        if (isQuickCastPressed && view.m_pOutdoorPartyRuntime != nullptr)
        {
            const bool hasReadyMember = view.m_pOutdoorPartyRuntime->party().hasSelectableMemberInGameplay();
            quickCastReadyMemberTransitionWhileHeld = !view.m_quickSpellReadyMemberAvailableWhileHeld && hasReadyMember;
            view.m_quickSpellReadyMemberAvailableWhileHeld = hasReadyMember;
        }
        else if (!isQuickCastPressed)
        {
            view.m_quickSpellReadyMemberAvailableWhileHeld = false;
        }

        const bool quickCastPressedThisFrame = isQuickCastPressed && !view.m_quickSpellCastLatch;
        const bool quickCastRepeatReady =
            isQuickCastPressed
            && view.m_quickSpellCastLatch
            && (view.m_quickSpellCastRepeatCooldownSeconds <= 0.0f || quickCastReadyMemberTransitionWhileHeld);

        if (quickCastPressedThisFrame || quickCastRepeatReady)
        {
            view.tryBeginQuickSpellCast();
            view.m_quickSpellCastLatch = true;
            view.m_quickSpellCastRepeatCooldownSeconds = OutdoorGameView::HeldGameplayActionRepeatDebounceSeconds;
        }
        else if (!isQuickCastPressed)
        {
            view.m_quickSpellCastLatch = false;
            view.m_quickSpellReadyMemberAvailableWhileHeld = false;
            view.m_quickSpellCastRepeatCooldownSeconds = 0.0f;
        }
    }
    else
    {
        view.m_quickSpellCastLatch = false;
        view.m_quickSpellReadyMemberAvailableWhileHeld = false;
        view.m_quickSpellCastRepeatCooldownSeconds = 0.0f;
    }

    if (isEventDialogActive)
    {
        return;
    }

    if (view.m_restScreen.active)
    {
        return;
    }

    if (view.m_spellbook.active)
    {
        return;
    }

    if (view.m_utilitySpellOverlay.active
        && view.m_utilitySpellOverlay.mode != OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget)
    {
        GameplayPartyOverlayInputController::handleUtilitySpellOverlayInput(
            view,
            pKeyboardState,
            screenWidth,
            screenHeight);
        return;
    }

    if (view.m_saveGameScreen.active)
    {
        return;
    }

    if (view.m_loadGameScreen.active)
    {
        const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_RETURN];

        if (closePressed)
        {
            if (!view.m_loadGameToggleLatch)
            {
                view.closeLoadGameScreen();
                view.m_loadGameToggleLatch = true;
            }
        }
        else
        {
            view.m_loadGameToggleLatch = false;
        }

        if (!view.m_loadGameScreen.active)
        {
            return;
        }

        float loadMouseX = 0.0f;
        float loadMouseY = 0.0f;
        const SDL_MouseButtonFlags loadMouseButtons = SDL_GetMouseState(&loadMouseX, &loadMouseY);
        const HudPointerState loadPointerState = {
            loadMouseX,
            loadMouseY,
            (loadMouseButtons & SDL_BUTTON_LMASK) != 0
        };
        const OutdoorGameView::SaveLoadPointerTarget noneLoadTarget = {};
        const auto resolveLoadTarget =
            [&view, screenWidth, screenHeight](
                const char *pLayoutId,
                OutdoorGameView::SaveLoadPointerTargetType type,
                float pointerX,
                float pointerY) -> OutdoorGameView::SaveLoadPointerTarget
            {
                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);

                if (pLayout == nullptr)
                {
                    return {};
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        pLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {};
                }

                OutdoorGameView::SaveLoadPointerTarget target = {};
                target.type = type;
                return target;
            };
        const auto findLoadPointerTarget =
            [&view, &resolveLoadTarget](float pointerX, float pointerY) -> OutdoorGameView::SaveLoadPointerTarget
            {
                for (size_t row = 0; row < SaveLoadVisibleSlotCount; ++row)
                {
                    const std::string layoutId = "LoadGameSlotRow" + std::to_string(row);
                    OutdoorGameView::SaveLoadPointerTarget target = resolveLoadTarget(
                        layoutId.c_str(),
                        OutdoorGameView::SaveLoadPointerTargetType::Slot,
                        pointerX,
                        pointerY);

                    if (target.type != OutdoorGameView::SaveLoadPointerTargetType::None)
                    {
                        target.slotIndex = view.m_loadGameScreen.scrollOffset + row;
                        return target;
                    }
                }

                OutdoorGameView::SaveLoadPointerTarget target = resolveLoadTarget(
                    "LoadGameScrollUpButton",
                    OutdoorGameView::SaveLoadPointerTargetType::ScrollUpButton,
                    pointerX,
                    pointerY);

                if (target.type != OutdoorGameView::SaveLoadPointerTargetType::None)
                {
                    return target;
                }

                target = resolveLoadTarget(
                    "LoadGameScrollDownButton",
                    OutdoorGameView::SaveLoadPointerTargetType::ScrollDownButton,
                    pointerX,
                    pointerY);

                if (target.type != OutdoorGameView::SaveLoadPointerTargetType::None)
                {
                    return target;
                }

                target = resolveLoadTarget(
                    "LoadGameConfirmButton",
                    OutdoorGameView::SaveLoadPointerTargetType::ConfirmButton,
                    pointerX,
                    pointerY);

                if (target.type != OutdoorGameView::SaveLoadPointerTargetType::None)
                {
                    return target;
                }

                return resolveLoadTarget(
                    "LoadGameCancelButton",
                    OutdoorGameView::SaveLoadPointerTargetType::CancelButton,
                    pointerX,
                    pointerY);
            };

        handlePointerClickRelease(
            loadPointerState,
            view.m_loadGameClickLatch,
            view.m_loadGamePressedTarget,
            noneLoadTarget,
            findLoadPointerTarget,
            [&view](const OutdoorGameView::SaveLoadPointerTarget &target)
            {
                switch (target.type)
                {
                case OutdoorGameView::SaveLoadPointerTargetType::Slot:
                    if (!view.m_loadGameScreen.slots.empty())
                    {
                        const size_t slotIndex =
                            std::min(target.slotIndex, view.m_loadGameScreen.slots.size() - 1);
                        view.m_loadGameScreen.selectedIndex = slotIndex;
                        const uint64_t nowTicks = SDL_GetTicks();

                        if (view.m_lastLoadGameClickedSlotIndex == slotIndex
                            && nowTicks - view.m_lastLoadGameSlotClickTicks <= SaveGameDoubleClickWindowMs)
                        {
                            view.tryLoadFromSelectedGameSlot();
                        }

                        view.m_lastLoadGameSlotClickTicks = nowTicks;
                        view.m_lastLoadGameClickedSlotIndex = slotIndex;
                    }
                    break;

                case OutdoorGameView::SaveLoadPointerTargetType::ScrollUpButton:
                    if (view.m_loadGameScreen.scrollOffset > 0)
                    {
                        --view.m_loadGameScreen.scrollOffset;
                    }
                    break;

                case OutdoorGameView::SaveLoadPointerTargetType::ScrollDownButton:
                    if (view.m_loadGameScreen.scrollOffset + SaveLoadVisibleSlotCount < view.m_loadGameScreen.slots.size())
                    {
                        ++view.m_loadGameScreen.scrollOffset;
                    }
                    break;

                case OutdoorGameView::SaveLoadPointerTargetType::ConfirmButton:
                    view.tryLoadFromSelectedGameSlot();
                    break;

                case OutdoorGameView::SaveLoadPointerTargetType::CancelButton:
                    view.closeLoadGameScreen();
                    break;

                case OutdoorGameView::SaveLoadPointerTargetType::None:
                    break;
                }
            });
        return;
    }

    if (view.m_controlsScreen.active)
    {
        return;
    }

    if (view.m_keyboardScreen.active)
    {
        return;
    }

    if (view.m_videoOptionsScreen.active)
    {
        return;
    }

    if (view.m_menuScreen.active)
    {
        return;
    }

    if (view.m_characterScreenOpen)
    {
        return;
    }

    view.interactionState().characterClickLatch = false;
    view.interactionState().characterMemberCycleLatch = false;
    view.interactionState().characterPressedTarget = {};
    view.closeReadableScrollOverlay();

    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool blockCameraRotation =
        view.m_buffInspectOverlay.active
        || view.m_characterDetailOverlay.active;

    if (view.m_gameplayMouseLookActive && !hasPendingSpellCast && !blockCameraRotation)
    {
        float deltaMouseX = 0.0f;
        float deltaMouseY = 0.0f;
        SDL_GetRelativeMouseState(&deltaMouseX, &deltaMouseY);

        if (deltaMouseX != 0.0f || deltaMouseY != 0.0f)
        {
            view.m_cameraYawRadians -= deltaMouseX * view.m_mouseRotateSpeed;
            view.m_cameraPitchRadians -= deltaMouseY * view.m_mouseRotateSpeed;
        }

        view.m_isRotatingCamera = true;
    }
    else
    {
        view.m_isRotatingCamera = false;
        view.m_lastMouseX = mouseX;
        view.m_lastMouseY = mouseY;
    }

    const float cosYaw = std::cos(view.m_cameraYawRadians);
    const float sinYaw = std::sin(view.m_cameraYawRadians);
    const bx::Vec3 forward = {
        cosYaw,
        sinYaw,
        0.0f
    };
    const bx::Vec3 right = {
        sinYaw,
        -cosYaw,
        0.0f
    };

    const bool moveForwardPressed = isActionPressed(KeyboardAction::Forward);
    const bool moveBackwardPressed = isActionPressed(KeyboardAction::Backward);
    const bool strafeLeftPressed = isActionPressed(KeyboardAction::Left);
    const bool strafeRightPressed = isActionPressed(KeyboardAction::Right);
    const bool jumpPressed = isActionPressed(KeyboardAction::Jump);
    const bool flyUpPressed = isActionPressed(KeyboardAction::FlyUp);
    const bool flyDownPressed = isActionPressed(KeyboardAction::FlyDown);
    const bool lookUpPressed = isActionPressed(KeyboardAction::LookUp);
    const bool lookDownPressed = isActionPressed(KeyboardAction::LookDown);
    const bool centerViewPressed = isActionPressed(KeyboardAction::CenterView);
    const bool landPressed = isActionPressed(KeyboardAction::Land);

    if (view.m_outdoorMapData)
    {
        if (view.m_pOutdoorPartyRuntime)
        {
            if (!hasActiveLootView && !hasPendingSpellCast && !view.m_gameplayCursorModeActive)
            {
                const OutdoorMovementInput movementInput = {
                    moveForwardPressed,
                    moveBackwardPressed,
                    strafeLeftPressed,
                    strafeRightPressed,
                    jumpPressed,
                    flyUpPressed,
                    (pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL]) || flyDownPressed,
                    turboSpeed,
                    view.m_cameraYawRadians,
                    view.m_cameraPitchRadians
                };
                if (view.m_pOutdoorSceneRuntime != nullptr)
                {
                    const OutdoorSceneRuntime::AdvanceFrameResult frameAdvanceResult =
                        view.m_pOutdoorSceneRuntime->advanceFrame(movementInput, deltaSeconds);

                    OutdoorInteractionController::applyPendingCombatEvents(view);

                    EventRuntimeState *pEventRuntimeState =
                        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

                    if (pEventRuntimeState != nullptr)
                    {
                        for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
                        {
                            view.setStatusBarEvent(statusMessage);
                        }

                        pEventRuntimeState->statusMessages.clear();
                    }

                    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

                    if (frameAdvanceResult.shouldOpenEventDialog)
                    {
                        OutdoorInteractionController::presentPendingEventDialog(view, frameAdvanceResult.previousMessageCount, true);
                    }
                }
            }

            view.m_cameraTargetX = view.m_pOutdoorPartyRuntime->movementState().x;
            view.m_cameraTargetY = view.m_pOutdoorPartyRuntime->movementState().y;
            view.m_cameraTargetZ = view.m_pOutdoorPartyRuntime->movementState().footZ + view.m_cameraEyeHeight;
        }
    }
    else
    {
        float moveVelocityX = 0.0f;
        float moveVelocityY = 0.0f;
        const float freeMoveSpeed = turboSpeed ? 4000.0f : 576.0f;

        if (!view.m_gameplayCursorModeActive && strafeLeftPressed)
        {
            moveVelocityX -= right.x * freeMoveSpeed;
            moveVelocityY -= right.y * freeMoveSpeed;
        }

        if (!view.m_gameplayCursorModeActive && strafeRightPressed)
        {
            moveVelocityX += right.x * freeMoveSpeed;
            moveVelocityY += right.y * freeMoveSpeed;
        }

        if (!view.m_gameplayCursorModeActive && moveForwardPressed)
        {
            moveVelocityX += forward.x * freeMoveSpeed;
            moveVelocityY += forward.y * freeMoveSpeed;
        }

        if (!view.m_gameplayCursorModeActive && moveBackwardPressed)
        {
            moveVelocityX -= forward.x * freeMoveSpeed;
            moveVelocityY -= forward.y * freeMoveSpeed;
        }

        view.m_cameraTargetX += moveVelocityX * deltaSeconds;
        view.m_cameraTargetY += moveVelocityY * deltaSeconds;
    }

    const float keyboardPitchSpeed = 1.25f;

    if (!view.m_gameplayCursorModeActive && lookUpPressed)
    {
        view.m_cameraPitchRadians -= keyboardPitchSpeed * deltaSeconds;
    }

    if (!view.m_gameplayCursorModeActive && lookDownPressed)
    {
        view.m_cameraPitchRadians += keyboardPitchSpeed * deltaSeconds;
    }

    if (!view.m_gameplayCursorModeActive && centerViewPressed)
    {
        view.m_cameraPitchRadians *= std::max(0.0f, 1.0f - deltaSeconds * 8.0f);
    }

    if (pKeyboardState[SDL_SCANCODE_1])
    {
        if (!view.m_toggleFilledLatch)
        {
            view.m_showFilledTerrain = !view.m_showFilledTerrain;
            view.m_toggleFilledLatch = true;
        }
    }
    else
    {
        view.m_toggleFilledLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_2])
    {
        if (!view.m_toggleWireframeLatch)
        {
            view.m_showTerrainWireframe = !view.m_showTerrainWireframe;
            view.m_toggleWireframeLatch = true;
        }
    }
    else
    {
        view.m_toggleWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_3])
    {
        if (!view.m_toggleBModelsLatch)
        {
            view.m_showBModels = !view.m_showBModels;
            view.m_toggleBModelsLatch = true;
        }
    }
    else
    {
        view.m_toggleBModelsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_4])
    {
        if (!view.m_toggleBModelWireframeLatch)
        {
            view.m_showBModelWireframe = !view.m_showBModelWireframe;
            view.m_toggleBModelWireframeLatch = true;
        }
    }
    else
    {
        view.m_toggleBModelWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_5])
    {
        if (!view.m_toggleBModelCollisionFacesLatch)
        {
            view.m_showBModelCollisionFaces = !view.m_showBModelCollisionFaces;
            view.m_toggleBModelCollisionFacesLatch = true;
        }
    }
    else
    {
        view.m_toggleBModelCollisionFacesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_6])
    {
        if (!view.m_toggleActorCollisionBoxesLatch)
        {
            view.m_showActorCollisionBoxes = !view.m_showActorCollisionBoxes;
            view.m_toggleActorCollisionBoxesLatch = true;
        }
    }
    else
    {
        view.m_toggleActorCollisionBoxesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_7])
    {
        if (!view.m_toggleActorsLatch)
        {
            view.m_showActors = !view.m_showActors;
            view.m_toggleActorsLatch = true;
        }
    }
    else
    {
        view.m_toggleActorsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F6])
    {
        if (!view.m_toggleSpriteObjectsLatch)
        {
            view.m_showSpriteObjects = !view.m_showSpriteObjects;
            view.m_toggleSpriteObjectsLatch = true;
        }
    }
    else
    {
        view.m_toggleSpriteObjectsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_9])
    {
        if (!view.m_toggleEntitiesLatch)
        {
            view.m_showEntities = !view.m_showEntities;
            view.m_toggleEntitiesLatch = true;
        }
    }
    else
    {
        view.m_toggleEntitiesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_0])
    {
        if (!view.m_toggleSpawnsLatch)
        {
            view.m_showSpawns = !view.m_showSpawns;
            view.m_toggleSpawnsLatch = true;
        }
    }
    else
    {
        view.m_toggleSpawnsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F2])
    {
        if (!view.m_toggleDebugHudLatch)
        {
            view.m_showDebugHud = !view.m_showDebugHud;
            view.m_toggleDebugHudLatch = true;
        }
    }
    else
    {
        view.m_toggleDebugHudLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F3])
    {
        if (!view.m_toggleDecorationBillboardsLatch)
        {
            view.m_showDecorationBillboards = !view.m_showDecorationBillboards;
            view.m_toggleDecorationBillboardsLatch = true;
        }
    }
    else
    {
        view.m_toggleDecorationBillboardsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F4])
    {
        if (!view.m_toggleGameplayHudLatch)
        {
            view.m_showGameplayHud = !view.m_showGameplayHud;
            view.m_toggleGameplayHudLatch = true;
        }
    }
    else
    {
        view.m_toggleGameplayHudLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F7])
    {
        if (!view.m_toggleTextureFilteringLatch)
        {
            toggleTextureFilteringEnabled();
            view.m_toggleTextureFilteringLatch = true;
        }
    }
    else
    {
        view.m_toggleTextureFilteringLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F5])
    {
        if (!view.m_toggleRainLatch)
        {
            if (view.m_pOutdoorWorldRuntime != nullptr)
            {
                view.m_pOutdoorWorldRuntime->cycleRainIntensityPreset();
                view.showStatusBarEvent(
                    std::string("Rain: ") + view.m_pOutdoorWorldRuntime->rainIntensityPresetName(),
                    2.0f);
            }

            view.m_toggleRainLatch = true;
        }
    }
    else
    {
        view.m_toggleRainLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_MINUS])
    {
        if (!view.m_toggleInspectLatch)
        {
            view.m_inspectMode = !view.m_inspectMode;
            view.m_toggleInspectLatch = true;
        }
    }
    else
    {
        view.m_toggleInspectLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_F1])
    {
        if (!view.m_triggerMeteorLatch)
        {
            const bool isDwiOutdoor =
                view.m_map.has_value()
                && view.m_map->id == DwiMapId
                && view.m_outdoorMapData.has_value()
                && view.m_pOutdoorSceneRuntime != nullptr
                && view.m_pOutdoorSceneRuntime->localEventProgram().has_value();

            if (isDwiOutdoor)
            {
                OutdoorInteractionController::tryTriggerLocalEventById(view, DwiMeteorShowerEventId);
            }

            view.m_triggerMeteorLatch = true;
        }
    }
    else
    {
        view.m_triggerMeteorLatch = false;
    }

    if (view.m_pOutdoorPartyRuntime)
    {
        if (pKeyboardState[SDL_SCANCODE_F])
        {
            if (!view.m_toggleFlyingLatch)
            {
                view.m_pOutdoorPartyRuntime->toggleFlying();
                view.m_toggleFlyingLatch = true;
            }
        }
        else
        {
            view.m_toggleFlyingLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_T])
        {
            if (!view.m_toggleWaterWalkLatch)
            {
                view.m_pOutdoorPartyRuntime->toggleWaterWalk();
                view.m_toggleWaterWalkLatch = true;
            }
        }
        else
        {
            view.m_toggleWaterWalkLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_G])
        {
            if (!view.m_toggleFeatherFallLatch)
            {
                view.m_pOutdoorPartyRuntime->toggleFeatherFall();
                view.m_toggleFeatherFallLatch = true;
            }
        }
        else
        {
            view.m_toggleFeatherFallLatch = false;
        }

        const SDL_Scancode landScancode = view.m_gameSettings.keyboard.binding(KeyboardAction::Land);

        if (landPressed
            && landScancode > SDL_SCANCODE_UNKNOWN
            && landScancode < SDL_SCANCODE_COUNT
            && view.previousKeyboardState()[landScancode] == 0
            && view.m_pOutdoorPartyRuntime->partyMovementState().flying)
        {
            view.m_pOutdoorPartyRuntime->toggleFlying();
        }
    }

    if (view.m_cameraYawRadians > Pi)
    {
        view.m_cameraYawRadians -= Pi * 2.0f;
    }
    else if (view.m_cameraYawRadians < -Pi)
    {
        view.m_cameraYawRadians += Pi * 2.0f;
    }

    view.m_cameraPitchRadians = std::clamp(view.m_cameraPitchRadians, -1.55f, 1.55f);
    view.m_cameraTargetZ = std::clamp(view.m_cameraTargetZ, -2000.0f, 30000.0f);
    view.m_cameraOrthoScale = std::clamp(view.m_cameraOrthoScale, 0.05f, 3.5f);
}
} // namespace OpenYAMM::Game
