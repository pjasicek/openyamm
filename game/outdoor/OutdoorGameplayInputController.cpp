#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/app/GameSettings.h"
#include "game/app/GameSession.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float FlyWheelHeightStep = 64.0f;
constexpr float MaxFlyWheelStepsPerFrame = 4.0f;
} // namespace

void OutdoorGameplayInputController::updateCameraFromInput(
    OutdoorGameView &view,
    const GameplayInputFrame &input,
    float deltaSeconds,
    GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics)
{
    const float displayDeltaSeconds = std::max(deltaSeconds, 0.000001f);
    const float instantaneousFramesPerSecond = 1.0f / displayDeltaSeconds;
    view.m_framesPerSecond = (view.m_framesPerSecond == 0.0f)
        ? instantaneousFramesPerSecond
        : (view.m_framesPerSecond * 0.9f + instantaneousFramesPerSecond * 0.1f);
    if (!input.turnBasedMovementStep)
    {
        deltaSeconds = std::min(deltaSeconds, 0.05f);
    }

    const float cameraDeltaSeconds = std::min(input.cameraDeltaSeconds.value_or(deltaSeconds), 0.05f);

    const bool *pKeyboardState = input.keyboardState();

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
    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    const GameplaySharedInputFrameResult &sharedInputFrameResult = view.m_gameSession.sharedInputFrameResult();
    view.syncGameplayMouseLookMode(pWindow, sharedInputFrameResult.mouseLookPolicy.mouseLookActive);

    if (sharedInputFrameResult.journalInputConsumed)
    {
        return;
    }

    if (sharedInputFrameResult.worldInputBlocked)
    {
        return;
    }

    const bool runWalkModifier = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const bool turboSpeed = input.turboMovementHeld();
    const bool blockCameraRotation =
        overlayContext.buffInspectOverlayReadOnly().active
        || overlayContext.characterDetailOverlayReadOnly().active;
    const bool wasRotatingCamera = view.m_isRotatingCamera;
    const bool classicControls = overlayContext.settingsSnapshot().controlScheme == ControlScheme::Classic;

    if (gameplayMouseLookState.mouseLookActive && !hasPendingSpellCast && !blockCameraRotation)
    {
        const float deltaMouseX = input.relativeMouseX;
        const float deltaMouseY = input.relativeMouseY;

        if (wasRotatingCamera && (deltaMouseX != 0.0f || deltaMouseY != 0.0f))
        {
            view.m_cameraYawRadians -= deltaMouseX * view.m_mouseRotateSpeed;
            view.m_cameraPitchRadians -= deltaMouseY * view.m_mouseRotateSpeed;
        }

        view.m_isRotatingCamera = true;
    }
    else
    {
        view.m_isRotatingCamera = false;
        view.m_lastMouseX = input.pointerX;
        view.m_lastMouseY = input.pointerY;
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

    const bool moveForwardPressed = input.action(KeyboardAction::Forward).held;
    const bool moveBackwardPressed = input.action(KeyboardAction::Backward).held;
    const bool leftPressed = input.action(KeyboardAction::Left).held;
    const bool rightPressed = input.action(KeyboardAction::Right).held;
    const bool strafeLeftPressed = !classicControls && leftPressed;
    const bool strafeRightPressed = !classicControls && rightPressed;
    const bool jumpPressed = input.action(KeyboardAction::Jump).held;
    const bool flyUpPressed = input.action(KeyboardAction::FlyUp).held;
    const bool flyDownPressed = input.action(KeyboardAction::FlyDown).held;
    const InputBindingKind wheelKind = mouseWheelInputBinding(input.mouseWheelDelta).kind;
    const bool wheelFlyUp = flyUpPressed
        && view.m_gameSettings.keyboard.binding(KeyboardAction::FlyUp).kind == wheelKind;
    const bool wheelFlyDown = flyDownPressed
        && view.m_gameSettings.keyboard.binding(KeyboardAction::FlyDown).kind == wheelKind;
    const float flyWheelSteps = std::min(std::abs(input.mouseWheelDelta), MaxFlyWheelStepsPerFrame);
    const float flyHeightDelta = FlyWheelHeightStep * flyWheelSteps * (int(wheelFlyUp) - int(wheelFlyDown));
    const bool lookUpPressed = input.action(KeyboardAction::LookUp).held;
    const bool lookDownPressed = input.action(KeyboardAction::LookDown).held;
    const bool centerViewPressed = input.action(KeyboardAction::CenterView).held;

    const bool allowWorldSimulation = !hasActiveLootView && !hasPendingSpellCast && !input.rightMouseButton.held;
    const bool allowCameraMovementInput = allowWorldSimulation && !gameplayMouseLookState.cursorModeActive;
    const float keyboardYawSpeed = 1.75f;

    if (classicControls && allowCameraMovementInput)
    {
        if (leftPressed)
        {
            view.m_cameraYawRadians += keyboardYawSpeed * cameraDeltaSeconds;
        }

        if (rightPressed)
        {
            view.m_cameraYawRadians -= keyboardYawSpeed * cameraDeltaSeconds;
        }
    }

    if (view.m_pOutdoorMapData)
    {
        if (view.m_pOutdoorPartyRuntime)
        {
            if (allowWorldSimulation)
            {
                // Named fields: a positional list put the wheel's flight step into partySpeedMultiplier when that
                // field was added before it, and the party runtime overwrote it (wheel flight did nothing).
                const OutdoorMovementInput movementInput = {
                    .forward = allowCameraMovementInput && moveForwardPressed,
                    .backward = allowCameraMovementInput && moveBackwardPressed,
                    .left = allowCameraMovementInput && strafeLeftPressed,
                    .right = allowCameraMovementInput && strafeRightPressed,
                    .jump = allowCameraMovementInput && jumpPressed,
                    .flyUp = allowCameraMovementInput && flyUpPressed && !wheelFlyUp,
                    .flyDown = allowCameraMovementInput && flyDownPressed && !wheelFlyDown,
                    .runWalkModifier = runWalkModifier,
                    .turbo = turboSpeed,
                    .yawRadians = view.m_cameraYawRadians,
                    .pitchRadians = view.m_cameraPitchRadians,
                    .usePitchForFlyingMovement = !classicControls,
                    .turnBasedMovementStep = input.turnBasedMovementStep,
                    .turnBasedPhysicsStep = input.turnBasedPhysicsStep,
                    .movementSpeedScale = input.movementSpeedScale,
                    .flyHeightDelta = allowCameraMovementInput ? flyHeightDelta : 0.0f,

                };
                if (view.m_pOutdoorSceneRuntime != nullptr)
                {
                    const OutdoorSceneRuntime::AdvanceFrameResult frameAdvanceResult =
                        view.m_pOutdoorSceneRuntime->advanceFrame(
                            movementInput,
                            deltaSeconds,
                            pPerformanceDiagnostics);

                    EventRuntimeState *pEventRuntimeState =
                        view.m_pOutdoorWorldRuntime != nullptr
                            ? view.m_pOutdoorWorldRuntime->eventRuntimeState()
                            : nullptr;

                    if (pEventRuntimeState != nullptr)
                    {
                        for (size_t index = 0; index < pEventRuntimeState->statusMessages.size(); ++index)
                        {
                            view.setStatusBarEvent(
                                pEventRuntimeState->statusMessages[index],
                                statusMessageSeconds(*pEventRuntimeState, index),
                                GameplayUiController::StatusBarEventPriority::High);
                        }

                        pEventRuntimeState->statusMessages.clear();
                        pEventRuntimeState->statusMessageSeconds.clear();
                    }

                    if (view.m_pOutdoorWorldRuntime != nullptr)
                    {
                        view.m_pOutdoorWorldRuntime->applyGrantedEventItemsToHeldInventory();
                    }

                    if (!view.m_pOutdoorPartyRuntime->movementStatusText().empty())
                    {
                        view.setStatusBarEvent(view.m_pOutdoorPartyRuntime->movementStatusText());
                    }

                    if (frameAdvanceResult.shouldOpenEventDialog)
                    {
                        if (view.m_pOutdoorWorldRuntime != nullptr)
                        {
                            view.m_pOutdoorWorldRuntime->presentPendingEventDialog(
                                frameAdvanceResult.previousMessageCount,
                                true);
                        }
                    }
                }
            }

            view.syncCameraToParty();
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

    // Positive pitch looks up.
    if (!gameplayMouseLookState.cursorModeActive && lookUpPressed)
    {
        view.m_cameraPitchRadians += keyboardPitchSpeed * cameraDeltaSeconds;
    }

    if (!gameplayMouseLookState.cursorModeActive && lookDownPressed)
    {
        view.m_cameraPitchRadians -= keyboardPitchSpeed * cameraDeltaSeconds;
    }

    if (!gameplayMouseLookState.cursorModeActive && centerViewPressed)
    {
        view.m_cameraPitchRadians *= std::max(0.0f, 1.0f - cameraDeltaSeconds * 8.0f);
    }

    if (view.m_pOutdoorPartyRuntime)
    {
        if (input.action(KeyboardAction::Land).pressed && view.m_pOutdoorPartyRuntime->partyMovementState().flying)
        {
            view.m_pOutdoorPartyRuntime->requestLanding();
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
