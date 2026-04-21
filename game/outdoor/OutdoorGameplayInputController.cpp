#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/app/GameSession.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/OutdoorSceneRuntime.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr int DwiMapId = 1;
constexpr uint16_t DwiMeteorShowerEventId = 456;
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

    const auto isActionPressed =
        [&view, pKeyboardState](KeyboardAction action) -> bool
        {
            return view.m_gameSettings.keyboard.isPressed(action, pKeyboardState);
        };
    GameplayScreenState &gameplayScreenState = view.m_gameSession.gameplayScreenState();
    GameplayScreenState::PendingSpellTargetState &pendingSpellCast = gameplayScreenState.pendingSpellTarget();
    GameplayScreenState::GameplayMouseLookState &gameplayMouseLookState =
        gameplayScreenState.gameplayMouseLookState();
    GameplayScreenRuntime &overlayContext = view.m_gameSession.gameplayScreenRuntime();
    const bool hasPendingSpellCast = pendingSpellCast.active;
    const bool hasActiveLootView =
        view.m_pOutdoorWorldRuntime != nullptr
        && (view.m_pOutdoorWorldRuntime->activeChestView() != nullptr
            || view.m_pOutdoorWorldRuntime->activeCorpseView() != nullptr);
    const bool isUtilitySpellModalActive =
        view.utilitySpellOverlay().active
        && view.utilitySpellOverlay().mode != OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget;
    const bool isReadableScrollOverlayActive = overlayContext.readableScrollOverlayReadOnly().active;
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
    const bool hasReadyMember =
        view.m_pOutdoorPartyRuntime != nullptr
        && view.m_pOutdoorPartyRuntime->party().hasSelectableMemberInGameplay();
    const GameplaySharedInputFrameResult sharedInputFrameResult =
        GameplayInputController::updateSharedGameplayInputFrame(
            gameplayScreenState,
            overlayContext,
            view.m_gameSession.gameplaySpellService(),
            GameplaySharedInputFrameConfig{
                .pKeyboardState = pKeyboardState,
                .mouseWheelDelta = mouseWheelDelta,
                .screenWidth = screenWidth,
                .screenHeight = screenHeight,
                .pointerX = gameplayMouseX,
                .pointerY = gameplayMouseY,
                .leftButtonPressed = (gameplayMouseButtons & SDL_BUTTON_LMASK) != 0,
                .rightButtonPressed = (gameplayMouseButtons & SDL_BUTTON_RMASK) != 0,
                .hasReadyMember = hasReadyMember,
                .canBeginQuickCast =
                    view.m_pOutdoorPartyRuntime != nullptr && view.m_pOutdoorWorldRuntime != nullptr,
                .isUtilitySpellModalActive = isUtilitySpellModalActive,
                .isReadableScrollOverlayActive = isReadableScrollOverlayActive,
                .buildSpellActionTargetQueries =
                    [&view]()
                    {
                        return view.buildSpellActionTargetQueries();
                    },
                .handlePendingSpellCastSucceeded =
                    [&view](const PartySpellCastResult &castResult)
                    {
                        view.m_outdoorFxRuntime.triggerPartySpellFx(view, castResult);
                        view.m_cachedHoverInspectHitValid = false;
                        view.m_cachedHoverInspectHit = {};
                    },
                .applyAlwaysRun =
                    [&view](bool enabled)
                    {
                        if (view.m_pOutdoorPartyRuntime != nullptr)
                        {
                            view.m_pOutdoorPartyRuntime->setRunning(enabled);
                        }
                    },
            });
    view.syncGameplayMouseLookMode(pWindow, sharedInputFrameResult.mouseLookPolicy.mouseLookActive);

    if (sharedInputFrameResult.journalInputConsumed)
    {
        return;
    }

    if (sharedInputFrameResult.worldInputBlocked)
    {
        return;
    }

    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    SDL_GetMouseState(&mouseX, &mouseY);
    const bool blockCameraRotation =
        overlayContext.buffInspectOverlayReadOnly().active
        || overlayContext.characterDetailOverlayReadOnly().active;

    if (gameplayMouseLookState.mouseLookActive && !hasPendingSpellCast && !blockCameraRotation)
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
            if (!hasActiveLootView && !hasPendingSpellCast && !gameplayMouseLookState.cursorModeActive)
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
                        view.m_pOutdoorWorldRuntime != nullptr
                            ? view.m_pOutdoorWorldRuntime->eventRuntimeState()
                            : nullptr;

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
                        OutdoorInteractionController::presentPendingEventDialog(
                            view,
                            frameAdvanceResult.previousMessageCount,
                            true);
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

        if (!gameplayMouseLookState.cursorModeActive && strafeLeftPressed)
        {
            moveVelocityX -= right.x * freeMoveSpeed;
            moveVelocityY -= right.y * freeMoveSpeed;
        }

        if (!gameplayMouseLookState.cursorModeActive && strafeRightPressed)
        {
            moveVelocityX += right.x * freeMoveSpeed;
            moveVelocityY += right.y * freeMoveSpeed;
        }

        if (!gameplayMouseLookState.cursorModeActive && moveForwardPressed)
        {
            moveVelocityX += forward.x * freeMoveSpeed;
            moveVelocityY += forward.y * freeMoveSpeed;
        }

        if (!gameplayMouseLookState.cursorModeActive && moveBackwardPressed)
        {
            moveVelocityX -= forward.x * freeMoveSpeed;
            moveVelocityY -= forward.y * freeMoveSpeed;
        }

        view.m_cameraTargetX += moveVelocityX * deltaSeconds;
        view.m_cameraTargetY += moveVelocityY * deltaSeconds;
    }

    const float keyboardPitchSpeed = 1.25f;

    if (!gameplayMouseLookState.cursorModeActive && lookUpPressed)
    {
        view.m_cameraPitchRadians -= keyboardPitchSpeed * deltaSeconds;
    }

    if (!gameplayMouseLookState.cursorModeActive && lookDownPressed)
    {
        view.m_cameraPitchRadians += keyboardPitchSpeed * deltaSeconds;
    }

    if (!gameplayMouseLookState.cursorModeActive && centerViewPressed)
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
