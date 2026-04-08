#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/ui/HudUiService.h"

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
constexpr int DwiMapId = 1;
constexpr uint16_t DwiMeteorShowerEventId = 456;
constexpr std::array<int, 3> JournalMapZoomLevels = {384, 768, 1536};
constexpr float JournalMapWorldHalfExtent = 32768.0f;

void clampJournalMapState(GameplayUiController::JournalScreenState &journalScreen)
{
    journalScreen.mapZoomStep = std::clamp(
        journalScreen.mapZoomStep,
        0,
        static_cast<int>(JournalMapZoomLevels.size()) - 1);

    const int zoom = JournalMapZoomLevels[journalScreen.mapZoomStep];
    const float zoomFactor = static_cast<float>(zoom) / 384.0f;
    const float visibleWorldHalfExtent = JournalMapWorldHalfExtent / zoomFactor;
    const float maxOffset = std::max(0.0f, JournalMapWorldHalfExtent - visibleWorldHalfExtent);
    journalScreen.mapCenterX = std::clamp(
        journalScreen.mapCenterX,
        -maxOffset,
        maxOffset);
    journalScreen.mapCenterY = std::clamp(
        journalScreen.mapCenterY,
        -maxOffset,
        maxOffset);
}


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
} // namespace

void OutdoorGameplayInputController::updateCameraFromInput(OutdoorGameView &view, float deltaSeconds)
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

    const bool hasActiveLootView =
        view.m_pOutdoorWorldRuntime != nullptr
        && (view.m_pOutdoorWorldRuntime->activeChestView() != nullptr
            || view.m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isEventDialogActive = view.hasActiveEventDialog();
    const bool hasPendingSpellCast = view.m_pendingSpellCast.active;
    const bool isSpellbookActive = view.m_spellbook.active;
    const bool isRestScreenActive = view.m_restScreen.active;
    const bool isJournalActive = view.m_journalScreen.active;
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

    if (view.m_pOutdoorPartyRuntime != nullptr
        && screenWidth > 0
        && screenHeight > 0
        && !isSpellbookActive
        && !isRestScreenActive
        && !isJournalActive)
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

    if (pKeyboardState[SDL_SCANCODE_C])
    {
        if (!view.m_spellbookToggleLatch)
        {
            if (view.m_spellbook.active)
            {
                view.closeSpellbook();
            }
            else if (!isEventDialogActive
                     && !view.m_characterScreenOpen
                     && !hasActiveLootView
                     && !hasPendingSpellCast
                     && !view.m_restScreen.active
                     && !view.m_journalScreen.active
                     && !view.m_heldInventoryItem.active)
            {
                view.openSpellbook();
            }

            view.m_spellbookToggleLatch = true;
        }
    }
    else
    {
        view.m_spellbookToggleLatch = false;
    }

    const bool canOpenRestScreen =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    if (canOpenRestScreen && pKeyboardState[SDL_SCANCODE_R])
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

    if (canOpenRestScreen && screenWidth > 0 && screenHeight > 0)
    {
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
            view.m_restClickLatch,
            view.m_restPressedTarget,
            noneRestTarget,
            [&view, screenWidth, screenHeight](float pointerX, float pointerY) -> OutdoorGameView::RestPointerTarget
            {
                const OutdoorGameView::HudLayoutElement *pLayout =
                    HudUiService::findHudLayoutElement(view, "OutdoorButtonRest");

                if (pLayout == nullptr)
                {
                    return {};
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        "OutdoorButtonRest",
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
        view.m_restClickLatch = false;
        view.m_restPressedTarget = {};
    }

    const bool canToggleAdventurersInn =
        !isEventDialogActive
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active
        && !view.m_heldInventoryItem.active;

    const bool canToggleJournal =
        !isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_restScreen.active
        && !view.m_heldInventoryItem.active;

    if (canToggleJournal && screenWidth > 0 && screenHeight > 0)
    {
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
            [&view, screenWidth, screenHeight](float pointerX, float pointerY) -> bool
            {
                const OutdoorGameView::HudLayoutElement *pLayout =
                    HudUiService::findHudLayoutElement(view, "OutdoorButtonBooks");

                if (pLayout == nullptr)
                {
                    return false;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    HudUiService::resolveHudLayoutElement(
                        view,
                        "OutdoorButtonBooks",
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

    if (pKeyboardState[SDL_SCANCODE_M])
    {
        if (!view.m_journalToggleLatch)
        {
            if (view.m_journalScreen.active)
            {
                view.closeJournal();
            }
            else if (canToggleJournal)
            {
                view.openJournal();
            }

            view.m_journalToggleLatch = true;
        }
    }
    else
    {
        view.m_journalToggleLatch = false;
    }

    if (canToggleAdventurersInn && pKeyboardState[SDL_SCANCODE_P])
    {
        if (!view.m_adventurersInnToggleLatch)
        {
            if (view.isAdventurersInnCharacterSourceActive())
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

    if (!isEventDialogActive && !view.m_restScreen.active && !view.m_journalScreen.active)
    {
        if (pKeyboardState[SDL_SCANCODE_I])
        {
            if (!view.m_inventoryScreenToggleLatch)
            {
                if (hasActiveLootView)
                {
                    if (view.m_inventoryNestedOverlay.active)
                    {
                        view.closeInventoryNestedOverlay();
                    }
                    else
                    {
                        view.openInventoryNestedOverlay(OutdoorGameView::InventoryNestedOverlayMode::ChestTransfer);
                    }
                }
                else
                {
                    view.m_characterScreenOpen = !view.m_characterScreenOpen;

                    if (view.m_characterScreenOpen)
                    {
                        view.m_adventurersInnRosterOverlayOpen = false;
                        view.m_characterScreenSource = OutdoorGameView::CharacterScreenSource::Party;
                        view.m_characterScreenSourceIndex = 0;
                        view.m_adventurersInnScrollOffset = 0;
                        view.m_characterPage = OutdoorGameView::CharacterPage::Inventory;
                        view.m_characterDollJewelryOverlayOpen = false;
                    }
                    else
                    {
                        view.m_characterDollJewelryOverlayOpen = false;
                        view.m_adventurersInnRosterOverlayOpen = false;
                    }
                }

                view.m_inventoryScreenToggleLatch = true;
            }
        }
        else
        {
            view.m_inventoryScreenToggleLatch = false;
        }
    }
    else
    {
        view.m_inventoryScreenToggleLatch = false;
    }

    if (!isEventDialogActive
        && !view.m_characterScreenOpen
        && !hasActiveLootView
        && !hasPendingSpellCast
        && !view.m_spellbook.active
        && !view.m_restScreen.active
        && !view.m_journalScreen.active)
    {
        if (pKeyboardState[SDL_SCANCODE_Q])
        {
            if (!view.m_quickSpellCastLatch)
            {
                view.tryBeginQuickSpellCast();
                view.m_quickSpellCastLatch = true;
            }
        }
        else
        {
            view.m_quickSpellCastLatch = false;
        }
    }
    else
    {
        view.m_quickSpellCastLatch = false;
    }

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

    if (isEventDialogActive)
    {
        GameplayOverlayContext overlayContext(view);
        GameplayOverlayInputController::handleDialogueOverlayInput(
            overlayContext,
            pKeyboardState,
            screenWidth,
            screenHeight,
            isResidentSelectionMode);
        return;
    }

    view.m_eventDialogSelectUpLatch = false;
    view.m_eventDialogSelectDownLatch = false;
    view.m_eventDialogAcceptLatch = false;
    view.m_eventDialogPartySelectLatches.fill(false);
    view.m_dialogueClickLatch = false;
    view.m_dialoguePressedTarget = {};

    if (view.m_restScreen.active)
    {
        const auto finishOrCloseRestScreen =
            [&view]()
            {
                const OutdoorGameView::RestMode mode = view.m_restScreen.mode;

                if (mode != OutdoorGameView::RestMode::None
                    && view.m_restScreen.remainingMinutes > 0.0f
                    && view.m_pOutdoorWorldRuntime != nullptr)
                {
                    view.m_pOutdoorWorldRuntime->advanceGameMinutes(view.m_restScreen.remainingMinutes);

                    if (mode == OutdoorGameView::RestMode::Heal && view.m_pOutdoorPartyRuntime != nullptr)
                    {
                        view.m_pOutdoorPartyRuntime->party().restAndHealAll();
                    }
                }

                view.closeRestScreen();
            };
        const auto waitUntilDawnMinutes =
            [&view]() -> float
            {
                if (view.m_pOutdoorWorldRuntime == nullptr)
                {
                    return 8.0f * 60.0f;
                }

                constexpr float DawnMinuteOfDay = 6.0f * 60.0f;
                const float minutesOfDay = std::fmod(
                    std::max(0.0f, view.m_pOutdoorWorldRuntime->gameMinutes()),
                    1440.0f);
                float targetMinuteOfDay = DawnMinuteOfDay;

                if (targetMinuteOfDay <= minutesOfDay)
                {
                    targetMinuteOfDay += 1440.0f;
                }

                return targetMinuteOfDay - minutesOfDay;
            };

        if (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E])
        {
            if (!view.m_closeOverlayLatch)
            {
                finishOrCloseRestScreen();
                view.m_closeOverlayLatch = true;
            }
        }
        else
        {
            view.m_closeOverlayLatch = false;
        }

        if (screenWidth > 0 && screenHeight > 0)
        {
            float restMouseX = 0.0f;
            float restMouseY = 0.0f;
            const SDL_MouseButtonFlags restMouseButtons = SDL_GetMouseState(&restMouseX, &restMouseY);
            const HudPointerState restPointerState = {
                restMouseX,
                restMouseY,
                (restMouseButtons & SDL_BUTTON_LMASK) != 0
            };
            const OutdoorGameView::RestPointerTarget noneRestTarget = {};
            const auto resolveRestButtonTarget =
                [&view, screenWidth, screenHeight](
                    const std::string &layoutId,
                    OutdoorGameView::RestPointerTargetType targetType,
                    float pointerX,
                    float pointerY) -> OutdoorGameView::RestPointerTarget
                {
                    const OutdoorGameView::HudLayoutElement *pLayout =
                        HudUiService::findHudLayoutElement(view, layoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                        HudUiService::resolveHudLayoutElement(
                            view,
                            layoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height);

                    if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {};
                    }

                    return {targetType};
                };
            const auto findRestPointerTarget =
                [&resolveRestButtonTarget](float pointerX, float pointerY) -> OutdoorGameView::RestPointerTarget
                {
                    const OutdoorGameView::RestPointerTarget rest8HoursTarget =
                        resolveRestButtonTarget(
                            "RestButton8Hours",
                            OutdoorGameView::RestPointerTargetType::Rest8HoursButton,
                            pointerX,
                            pointerY);

                    if (rest8HoursTarget.type != OutdoorGameView::RestPointerTargetType::None)
                    {
                        return rest8HoursTarget;
                    }

                    const OutdoorGameView::RestPointerTarget dawnTarget =
                        resolveRestButtonTarget(
                            "RestButtonUntilDawn",
                            OutdoorGameView::RestPointerTargetType::WaitUntilDawnButton,
                            pointerX,
                            pointerY);

                    if (dawnTarget.type != OutdoorGameView::RestPointerTargetType::None)
                    {
                        return dawnTarget;
                    }

                    const OutdoorGameView::RestPointerTarget oneHourTarget =
                        resolveRestButtonTarget(
                            "RestButton1Hour",
                            OutdoorGameView::RestPointerTargetType::Wait1HourButton,
                            pointerX,
                            pointerY);

                    if (oneHourTarget.type != OutdoorGameView::RestPointerTargetType::None)
                    {
                        return oneHourTarget;
                    }

                    const OutdoorGameView::RestPointerTarget fiveMinutesTarget =
                        resolveRestButtonTarget(
                            "RestButton5Minutes",
                            OutdoorGameView::RestPointerTargetType::Wait5MinutesButton,
                            pointerX,
                            pointerY);

                    if (fiveMinutesTarget.type != OutdoorGameView::RestPointerTargetType::None)
                    {
                        return fiveMinutesTarget;
                    }

                    return resolveRestButtonTarget(
                        "RestButtonExit",
                        OutdoorGameView::RestPointerTargetType::ExitButton,
                        pointerX,
                        pointerY);
                };

            handlePointerClickRelease(
                restPointerState,
                view.m_restClickLatch,
                view.m_restPressedTarget,
                noneRestTarget,
                findRestPointerTarget,
                [&view, &finishOrCloseRestScreen, &waitUntilDawnMinutes](
                    const OutdoorGameView::RestPointerTarget &target)
                {
                    switch (target.type)
                    {
                        case OutdoorGameView::RestPointerTargetType::Rest8HoursButton:
                            view.startRestAction(OutdoorGameView::RestMode::Heal, 8.0f * 60.0f);
                            break;

                        case OutdoorGameView::RestPointerTargetType::WaitUntilDawnButton:
                            view.startRestAction(OutdoorGameView::RestMode::Wait, waitUntilDawnMinutes());
                            break;

                        case OutdoorGameView::RestPointerTargetType::Wait1HourButton:
                            view.startRestAction(OutdoorGameView::RestMode::Wait, 60.0f);
                            break;

                        case OutdoorGameView::RestPointerTargetType::Wait5MinutesButton:
                            view.startRestAction(OutdoorGameView::RestMode::Wait, 5.0f);
                            break;

                        case OutdoorGameView::RestPointerTargetType::ExitButton:
                            finishOrCloseRestScreen();
                            break;

                        case OutdoorGameView::RestPointerTargetType::None:
                        case OutdoorGameView::RestPointerTargetType::OpenButton:
                            break;
                    }
                });
        }
        else
        {
            view.m_restClickLatch = false;
            view.m_restPressedTarget = {};
        }

        return;
    }

    if (view.m_journalScreen.active)
    {
        const auto adjustPage =
            [&view](int delta)
            {
                if (view.m_journalScreen.view == OutdoorGameView::JournalView::Quests)
                {
                    if (delta < 0 && view.m_journalScreen.questPage > 0)
                    {
                        --view.m_journalScreen.questPage;
                    }
                    else if (delta > 0)
                    {
                        ++view.m_journalScreen.questPage;
                    }
                }
                else if (view.m_journalScreen.view == OutdoorGameView::JournalView::Story)
                {
                    if (delta < 0 && view.m_journalScreen.storyPage > 0)
                    {
                        --view.m_journalScreen.storyPage;
                    }
                    else if (delta > 0)
                    {
                        ++view.m_journalScreen.storyPage;
                    }
                }
                else if (view.m_journalScreen.view == OutdoorGameView::JournalView::Notes)
                {
                    if (delta < 0 && view.m_journalScreen.notesPage > 0)
                    {
                        --view.m_journalScreen.notesPage;
                    }
                    else if (delta > 0)
                    {
                        ++view.m_journalScreen.notesPage;
                    }
                }
            };

        if (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E])
        {
            if (!view.m_closeOverlayLatch)
            {
                view.closeJournal();
                view.m_closeOverlayLatch = true;
            }
        }
        else
        {
            view.m_closeOverlayLatch = false;
        }

        if (screenWidth > 0 && screenHeight > 0)
        {
            float journalMouseX = 0.0f;
            float journalMouseY = 0.0f;
            const SDL_MouseButtonFlags journalMouseButtons = SDL_GetMouseState(&journalMouseX, &journalMouseY);
            const HudPointerState journalPointerState = {
                journalMouseX,
                journalMouseY,
                (journalMouseButtons & SDL_BUTTON_LMASK) != 0
            };
            const OutdoorGameView::JournalPointerTarget noneJournalTarget = {};

            const auto resolveJournalTarget =
                [&view, screenWidth, screenHeight](
                    const std::string &layoutId,
                    OutdoorGameView::JournalPointerTargetType targetType,
                    float pointerX,
                    float pointerY) -> OutdoorGameView::JournalPointerTarget
                {
                    const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                        HudUiService::resolveHudLayoutElement(
                            view,
                            layoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height);

                    if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {};
                    }

                    return {targetType};
                };

            const auto findJournalPointerTarget =
                [&view, &resolveJournalTarget](float pointerX, float pointerY) -> OutdoorGameView::JournalPointerTarget
                {
                    static const std::pair<const char *, OutdoorGameView::JournalPointerTargetType> CommonTargets[] = {
                        {"JournalMainViewMap", OutdoorGameView::JournalPointerTargetType::MainMapView},
                        {"JournalMainViewQuests", OutdoorGameView::JournalPointerTargetType::MainQuestsView},
                        {"JournalMainViewStory", OutdoorGameView::JournalPointerTargetType::MainStoryView},
                        {"JournalMainViewNotes", OutdoorGameView::JournalPointerTargetType::MainNotesView},
                        {"JournalCloseButton", OutdoorGameView::JournalPointerTargetType::CloseButton},
                    };
                    static const std::pair<const char *, OutdoorGameView::JournalPointerTargetType> MapTargets[] = {
                        {"JournalMapZoomInButton", OutdoorGameView::JournalPointerTargetType::MapZoomInButton},
                        {"JournalMapZoomOutButton", OutdoorGameView::JournalPointerTargetType::MapZoomOutButton},
                    };
                    static const std::pair<const char *, OutdoorGameView::JournalPointerTargetType> PageTargets[] = {
                        {"JournalPrevPageButton", OutdoorGameView::JournalPointerTargetType::PrevPageButton},
                        {"JournalNextPageButton", OutdoorGameView::JournalPointerTargetType::NextPageButton},
                    };
                    static const std::pair<const char *, OutdoorGameView::JournalPointerTargetType> NotesTargets[] = {
                        {"JournalNotesPotionButton", OutdoorGameView::JournalPointerTargetType::NotesPotionButton},
                        {"JournalNotesFountainButton", OutdoorGameView::JournalPointerTargetType::NotesFountainButton},
                        {"JournalNotesObeliskButton", OutdoorGameView::JournalPointerTargetType::NotesObeliskButton},
                        {"JournalNotesSeerButton", OutdoorGameView::JournalPointerTargetType::NotesSeerButton},
                        {"JournalNotesMiscButton", OutdoorGameView::JournalPointerTargetType::NotesMiscButton},
                        {"JournalNotesTrainerButton", OutdoorGameView::JournalPointerTargetType::NotesTrainerButton},
                    };

                    for (const auto &[layoutId, targetType] : CommonTargets)
                    {
                        const OutdoorGameView::JournalPointerTarget target =
                            resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                        if (target.type != OutdoorGameView::JournalPointerTargetType::None)
                        {
                            return target;
                        }
                    }

                    if (view.m_journalScreen.view == OutdoorGameView::JournalView::Map)
                    {
                        for (const auto &[layoutId, targetType] : MapTargets)
                        {
                            const OutdoorGameView::JournalPointerTarget target =
                                resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                            if (target.type != OutdoorGameView::JournalPointerTargetType::None)
                            {
                                return target;
                            }
                        }
                    }
                    else
                    {
                        for (const auto &[layoutId, targetType] : PageTargets)
                        {
                            const OutdoorGameView::JournalPointerTarget target =
                                resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                            if (target.type != OutdoorGameView::JournalPointerTargetType::None)
                            {
                                return target;
                            }
                        }

                        if (view.m_journalScreen.view == OutdoorGameView::JournalView::Notes)
                        {
                            for (const auto &[layoutId, targetType] : NotesTargets)
                            {
                                const OutdoorGameView::JournalPointerTarget target =
                                    resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                                if (target.type != OutdoorGameView::JournalPointerTargetType::None)
                                {
                                    return target;
                                }
                            }
                        }
                    }

                    return {};
                };

            const auto resolveJournalViewport =
                [&view, screenWidth, screenHeight]() -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
                {
                    const OutdoorGameView::HudLayoutElement *pLayout =
                        HudUiService::findHudLayoutElement(view, "JournalMapViewport");

                    if (pLayout == nullptr)
                    {
                        return std::nullopt;
                    }

                    return HudUiService::resolveHudLayoutElement(
                        view,
                        "JournalMapViewport",
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);
                };

            const auto activateJournalTarget =
                [&view, &adjustPage](const OutdoorGameView::JournalPointerTarget &target)
                {
                    switch (target.type)
                    {
                        case OutdoorGameView::JournalPointerTargetType::MainMapView:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MainQuestsView:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Quests;
                            view.m_journalScreen.mapDragActive = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MainStoryView:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Story;
                            view.m_journalScreen.mapDragActive = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MainNotesView:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.mapDragActive = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::PrevPageButton:
                            adjustPage(-1);
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NextPageButton:
                            adjustPage(1);
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesPotionButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Potion;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesFountainButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Fountain;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesObeliskButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Obelisk;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesSeerButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Seer;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesMiscButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Misc;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::NotesTrainerButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Notes;
                            view.m_journalScreen.notesCategory = OutdoorGameView::JournalNotesCategory::Trainer;
                            view.m_journalScreen.notesPage = 0;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapZoomInButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapZoomStep = std::min(
                                view.m_journalScreen.mapZoomStep + 1,
                                static_cast<int>(JournalMapZoomLevels.size()) - 1);

                            if (view.m_pOutdoorPartyRuntime != nullptr)
                            {
                                const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
                                view.m_journalScreen.mapCenterX = moveState.x;
                                view.m_journalScreen.mapCenterY = moveState.y;
                            }

                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapZoomOutButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapZoomStep = std::max(view.m_journalScreen.mapZoomStep - 1, 0);

                            if (view.m_pOutdoorPartyRuntime != nullptr)
                            {
                                const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
                                view.m_journalScreen.mapCenterX = moveState.x;
                                view.m_journalScreen.mapCenterY = moveState.y;
                            }

                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapPanNorthButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapCenterY += 512.0f;
                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapPanSouthButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapCenterY -= 512.0f;
                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapPanEastButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapCenterX -= 512.0f;
                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::MapPanWestButton:
                            view.m_journalScreen.view = OutdoorGameView::JournalView::Map;
                            view.m_journalScreen.mapCenterX += 512.0f;
                            clampJournalMapState(view.m_journalScreen);
                            view.m_cachedJournalMapValid = false;
                            break;
                        case OutdoorGameView::JournalPointerTargetType::CloseButton:
                            view.closeJournal();
                            break;
                        case OutdoorGameView::JournalPointerTargetType::None:
                            break;
                    }
                };

            const auto isImmediateJournalMapTarget =
                [](const OutdoorGameView::JournalPointerTarget &target) -> bool
                {
                    switch (target.type)
                    {
                        case OutdoorGameView::JournalPointerTargetType::MapZoomInButton:
                        case OutdoorGameView::JournalPointerTargetType::MapZoomOutButton:
                        case OutdoorGameView::JournalPointerTargetType::MapPanNorthButton:
                        case OutdoorGameView::JournalPointerTargetType::MapPanSouthButton:
                        case OutdoorGameView::JournalPointerTargetType::MapPanEastButton:
                        case OutdoorGameView::JournalPointerTargetType::MapPanWestButton:
                            return true;

                        case OutdoorGameView::JournalPointerTargetType::None:
                        case OutdoorGameView::JournalPointerTargetType::MainMapView:
                        case OutdoorGameView::JournalPointerTargetType::MainQuestsView:
                        case OutdoorGameView::JournalPointerTargetType::MainStoryView:
                        case OutdoorGameView::JournalPointerTargetType::MainNotesView:
                        case OutdoorGameView::JournalPointerTargetType::PrevPageButton:
                        case OutdoorGameView::JournalPointerTargetType::NextPageButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesPotionButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesFountainButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesObeliskButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesSeerButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesMiscButton:
                        case OutdoorGameView::JournalPointerTargetType::NotesTrainerButton:
                        case OutdoorGameView::JournalPointerTargetType::CloseButton:
                            return false;
                    }

                    return false;
                };

            if (view.m_journalScreen.mapDragActive)
            {
                if (journalPointerState.leftButtonPressed)
                {
                    const int zoom = JournalMapZoomLevels[view.m_journalScreen.mapZoomStep];
                    const float zoomFactor = static_cast<float>(zoom) / 384.0f;
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> mapViewport = resolveJournalViewport();
                    const float viewportWidth = mapViewport.has_value() ? mapViewport->width : 336.0f;
                    const float viewportHeight = mapViewport.has_value() ? mapViewport->height : 336.0f;
                    const float worldUnitsPerPixelX =
                        (JournalMapWorldHalfExtent * 2.0f) / (zoomFactor * std::max(1.0f, viewportWidth));
                    const float worldUnitsPerPixelY =
                        (JournalMapWorldHalfExtent * 2.0f) / (zoomFactor * std::max(1.0f, viewportHeight));
                    const float deltaX = journalPointerState.x - view.m_journalScreen.mapDragStartMouseX;
                    const float deltaY = journalPointerState.y - view.m_journalScreen.mapDragStartMouseY;
                    const float previousCenterX = view.m_journalScreen.mapCenterX;
                    const float previousCenterY = view.m_journalScreen.mapCenterY;

                    view.m_journalScreen.mapCenterX =
                        view.m_journalScreen.mapDragStartCenterX - deltaX * worldUnitsPerPixelX;
                    view.m_journalScreen.mapCenterY =
                        view.m_journalScreen.mapDragStartCenterY - deltaY * worldUnitsPerPixelY;
                    clampJournalMapState(view.m_journalScreen);

                    if (std::abs(view.m_journalScreen.mapCenterX - previousCenterX) > 0.01f
                        || std::abs(view.m_journalScreen.mapCenterY - previousCenterY) > 0.01f)
                    {
                        view.m_cachedJournalMapValid = false;
                    }
                }
                else
                {
                    view.m_journalScreen.mapDragActive = false;
                    view.m_journalClickLatch = false;
                    view.m_journalPressedTarget = noneJournalTarget;
                }

                return;
            }

            if (journalPointerState.leftButtonPressed && !view.m_journalClickLatch)
            {
                const OutdoorGameView::JournalPointerTarget pressedTarget =
                    findJournalPointerTarget(journalPointerState.x, journalPointerState.y);

                if (isImmediateJournalMapTarget(pressedTarget))
                {
                    activateJournalTarget(pressedTarget);
                    view.m_journalClickLatch = true;
                    view.m_journalPressedTarget = noneJournalTarget;
                    return;
                }

                if (view.m_journalScreen.view == OutdoorGameView::JournalView::Map && pressedTarget == noneJournalTarget)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> mapViewport = resolveJournalViewport();

                    if (mapViewport.has_value()
                        && HudUiService::isPointerInsideResolvedElement(
                            *mapViewport,
                            journalPointerState.x,
                            journalPointerState.y))
                    {
                        view.m_journalScreen.mapDragActive = true;
                        view.m_journalScreen.mapDragStartMouseX = journalPointerState.x;
                        view.m_journalScreen.mapDragStartMouseY = journalPointerState.y;
                        view.m_journalScreen.mapDragStartCenterX = view.m_journalScreen.mapCenterX;
                        view.m_journalScreen.mapDragStartCenterY = view.m_journalScreen.mapCenterY;
                        view.m_journalClickLatch = true;
                        view.m_journalPressedTarget = noneJournalTarget;
                        return;
                    }
                }
            }

            handlePointerClickRelease(
                journalPointerState,
                view.m_journalClickLatch,
                view.m_journalPressedTarget,
                noneJournalTarget,
                findJournalPointerTarget,
                activateJournalTarget);
        }
        else
        {
            view.m_journalClickLatch = false;
            view.m_journalPressedTarget = {};
        }

        return;
    }

    if (view.m_spellbook.active)
    {
        GameplayPartyOverlayInputController::handleSpellbookOverlayInput(view, pKeyboardState, screenWidth, screenHeight);
        return;
    }

    if (view.m_characterScreenOpen)
    {
        GameplayPartyOverlayInputController::handleCharacterOverlayInput(view, pKeyboardState, screenWidth, screenHeight);
        return;
    }

    view.m_characterClickLatch = false;
    view.m_characterMemberCycleLatch = false;
    view.m_characterPressedTarget = {};
    view.closeReadableScrollOverlay();

    GameplayOverlayContext overlayContext(view);
    GameplayOverlayInputController::handleLootOverlayInput(
        overlayContext,
        pKeyboardState,
        screenWidth,
        screenHeight,
        hasActiveLootView);

    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const float mouseRotateSpeed = 0.0045f;
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isRightMousePressed = (mouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool blockCameraRotation =
        view.m_buffInspectOverlay.active
        || view.m_characterDetailOverlay.active;

    if (isRightMousePressed && !hasPendingSpellCast && !blockCameraRotation)
    {
        if (view.m_isRotatingCamera)
        {
            const float deltaMouseX = mouseX - view.m_lastMouseX;
            const float deltaMouseY = mouseY - view.m_lastMouseY;
            view.m_cameraYawRadians -= deltaMouseX * mouseRotateSpeed;
            view.m_cameraPitchRadians -= deltaMouseY * mouseRotateSpeed;
        }

        view.m_isRotatingCamera = true;
        view.m_lastMouseX = mouseX;
        view.m_lastMouseY = mouseY;
    }
    else
    {
        view.m_isRotatingCamera = false;
    }

    const float cosYaw = std::cos(view.m_cameraYawRadians);
    const float sinYaw = std::sin(view.m_cameraYawRadians);
    const bx::Vec3 forward = {
        cosYaw,
        -sinYaw,
        0.0f
    };
    const bx::Vec3 right = {
        sinYaw,
        cosYaw,
        0.0f
    };

    if (view.m_outdoorMapData)
    {
        if (view.m_pOutdoorPartyRuntime)
        {
            if (!hasActiveLootView && !hasPendingSpellCast)
            {
                const OutdoorMovementInput movementInput = {
                    pKeyboardState[SDL_SCANCODE_W],
                    pKeyboardState[SDL_SCANCODE_S],
                    pKeyboardState[SDL_SCANCODE_A],
                    pKeyboardState[SDL_SCANCODE_D],
                    pKeyboardState[SDL_SCANCODE_X],
                    pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL],
                    turboSpeed,
                    view.m_cameraYawRadians
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

        if (pKeyboardState[SDL_SCANCODE_A])
        {
            moveVelocityX -= right.x * freeMoveSpeed;
            moveVelocityY -= right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_D])
        {
            moveVelocityX += right.x * freeMoveSpeed;
            moveVelocityY += right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_W])
        {
            moveVelocityX += forward.x * freeMoveSpeed;
            moveVelocityY += forward.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_S])
        {
            moveVelocityX -= forward.x * freeMoveSpeed;
            moveVelocityY -= forward.y * freeMoveSpeed;
        }

        view.m_cameraTargetX += moveVelocityX * deltaSeconds;
        view.m_cameraTargetY += moveVelocityY * deltaSeconds;
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

    if (pKeyboardState[SDL_SCANCODE_F5])
    {
        if (!view.m_debugDialogueLatch)
        {
            OutdoorInteractionController::openDebugNpcDialogue(view, 31);
            view.m_debugDialogueLatch = true;
        }
    }
    else
    {
        view.m_debugDialogueLatch = false;
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
                && view.m_pOutdoorSceneRuntime->localEventIrProgram().has_value();

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
        view.m_toggleRunningLatch = false;

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
