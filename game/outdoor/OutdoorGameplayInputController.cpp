#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/ui/HudUiService.h"

#include <SDL3/SDL.h>

#include <algorithm>
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
        && !isRestScreenActive)
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
            && !isRestScreenActive;

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
        && !view.m_heldInventoryItem.active;

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

    if (!isEventDialogActive && !view.m_restScreen.active)
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
        && !view.m_restScreen.active)
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
