#include "game/outdoor/OutdoorGameplayInputController.h"

#include "game/app/GameSettings.h"
#include "game/app/GameSession.h"
#include "game/data/GameDataRepository.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/scene/OutdoorSceneRuntime.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float ArpgModeMeleeAutoTargetDistance = 407.2f;
constexpr float ArpgModeCameraMinDistance = 800.0f;
constexpr float ArpgModeCameraMaxDistance = 6400.0f;
constexpr float ArpgModeCameraWheelStep = 220.0f;

float normalizedDegrees(float degrees)
{
    float normalized = std::fmod(degrees, 360.0f);

    if (normalized < 0.0f)
    {
        normalized += 360.0f;
    }

    return normalized;
}

float radiansToNormalizedDegrees(float radians)
{
    return normalizedDegrees(radians * 180.0f / Pi);
}

void logArpgModeDirectionDiagnostic(
    bool moveForward,
    float movementYawRadians,
    bool hasActualMovementYaw,
    float actualMovementYawRadians,
    float facingYawRadians,
    float minimapArrowYawRadians,
    float deltaSeconds)
{
    static float elapsedSeconds = 0.0f;
    elapsedSeconds += std::max(0.0f, deltaSeconds);

    if (elapsedSeconds < 1.0f)
    {
        return;
    }

    elapsedSeconds = 0.0f;

    std::cout
        << "[ArpgModeDirection]"
        << " moving=" << (moveForward ? "true" : "false")
        << " intended_go_degrees=" << radiansToNormalizedDegrees(movementYawRadians)
        << " actual_go_degrees="
        << (hasActualMovementYaw ? std::to_string(radiansToNormalizedDegrees(actualMovementYawRadians)) : "none")
        << " facing_degrees=" << radiansToNormalizedDegrees(facingYawRadians)
        << " minimap_arrow_degrees=" << radiansToNormalizedDegrees(minimapArrowYawRadians)
        << '\n';
}

bool arpgModeActiveMemberUsesPlainMelee(OutdoorGameView &view)
{
    IGameplayWorldRuntime *pWorldRuntime = view.worldRuntime();
    OutdoorWorldRuntime *pOutdoorWorldRuntime = static_cast<OutdoorWorldRuntime *>(pWorldRuntime);

    if (pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    Party *pParty = pOutdoorWorldRuntime->party();
    Character *pAttacker = pParty != nullptr ? pParty->activeMember() : nullptr;

    if (pAttacker == nullptr || !pAttacker->attackSpellName.empty())
    {
        return false;
    }

    const CharacterAttackProfile profile =
        GameMechanics::buildCharacterAttackProfile(
            *pAttacker,
            &view.data().itemTable(),
            &view.data().spellTable(),
            CharacterAttackTuning{});

    return profile.canMelee
        && !profile.hasBow
        && !profile.hasWand
        && !profile.hasBlaster
        && !profile.hasDragonBreath
        && !profile.rangedAttackBonus.has_value();
}

std::optional<bx::Vec3> resolveArpgModeNearestMeleeTarget(OutdoorGameView &view)
{
    IGameplayWorldRuntime *pWorldRuntime = view.worldRuntime();
    OutdoorWorldRuntime *pOutdoorWorldRuntime = static_cast<OutdoorWorldRuntime *>(pWorldRuntime);
    OutdoorPartyRuntime *pPartyRuntime = view.partyRuntime();

    if (pOutdoorWorldRuntime == nullptr || pPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    if (!arpgModeActiveMemberUsesPlainMelee(view))
    {
        return std::nullopt;
    }

    const OutdoorMoveState &moveState = pPartyRuntime->movementState();
    float bestDistanceSquared = ArpgModeMeleeAutoTargetDistance * ArpgModeMeleeAutoTargetDistance;
    std::optional<bx::Vec3> bestTarget;

    for (size_t actorIndex = 0; actorIndex < pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActor == nullptr
            || pActor->isDead
            || pActor->currentHp <= 0
            || pActor->isInvisible
            || !pActor->hostileToParty)
        {
            continue;
        }

        const float deltaX = pActor->preciseX - moveState.x;
        const float deltaY = pActor->preciseY - moveState.y;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

        if (distanceSquared < bestDistanceSquared)
        {
            bestDistanceSquared = distanceSquared;
            bestTarget = bx::Vec3{
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f
            };
        }
    }

    return bestTarget;
}
} // namespace

void OutdoorGameplayInputController::applyOutdoorFrameAdvanceResult(
    OutdoorGameView &view,
    const OutdoorSceneRuntime::AdvanceFrameResult &result)
{
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

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        view.m_pOutdoorWorldRuntime->applyGrantedEventItemsToHeldInventory();
    }

    if (view.m_pOutdoorPartyRuntime != nullptr && !view.m_pOutdoorPartyRuntime->movementStatusText().empty())
    {
        view.setStatusBarEvent(view.m_pOutdoorPartyRuntime->movementStatusText());
    }

    if (result.shouldOpenEventDialog && view.m_pOutdoorWorldRuntime != nullptr)
    {
        view.m_pOutdoorWorldRuntime->presentPendingEventDialog(result.previousMessageCount, true);
    }
}

std::optional<bx::Vec3> OutdoorGameplayInputController::resolveArpgModeMoveClick(
    OutdoorGameView &view,
    const GameplayInputFrame &input)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const GameplayWorldPickRequest pickRequest =
        view.m_pOutdoorWorldRuntime->buildWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = input.pointerX,
                .screenY = input.pointerY,
                .screenWidth = input.screenWidth,
                .screenHeight = input.screenHeight,
                .includeRay = true,
            });
    const GameplayWorldHit hit = view.m_pOutdoorWorldRuntime->pickMouseInteractionTarget(pickRequest);

    if (hit.kind == GameplayWorldHitKind::Ground && hit.ground && hit.ground->isValid)
    {
        return hit.ground->worldPoint;
    }

    const GameplayPendingSpellWorldTargetFacts targetFacts =
        view.m_pOutdoorWorldRuntime->pickPendingSpellWorldTarget(pickRequest);
    return targetFacts.fallbackGroundTargetPoint;
}

void OutdoorGameplayInputController::faceArpgModePointerDirection(
    OutdoorGameView &view,
    const GameplayInputFrame &input)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const GameplayWorldPickRequest pickRequest =
        view.m_pOutdoorWorldRuntime->buildWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = input.pointerX,
                .screenY = input.pointerY,
                .screenWidth = input.screenWidth,
                .screenHeight = input.screenHeight,
                .includeRay = true,
            });

    const GameplayPendingSpellWorldTargetFacts targetFacts =
        view.m_pOutdoorWorldRuntime->pickPendingSpellWorldTarget(pickRequest);

    if (!targetFacts.fallbackGroundTargetPoint || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
    const float deltaX = targetFacts.fallbackGroundTargetPoint->x - moveState.x;
    const float deltaY = targetFacts.fallbackGroundTargetPoint->y - moveState.y;
    const float horizontalLengthSquared = deltaX * deltaX + deltaY * deltaY;

    if (horizontalLengthSquared <= 0.000001f)
    {
        return;
    }

    view.m_cameraYawRadians = std::atan2(deltaY, deltaX);
}

bool faceArpgModeNearestMeleeTarget(OutdoorGameView &view)
{
    const std::optional<bx::Vec3> target = resolveArpgModeNearestMeleeTarget(view);

    OutdoorPartyRuntime *pPartyRuntime = view.partyRuntime();

    if (!target || pPartyRuntime == nullptr)
    {
        return false;
    }

    const OutdoorMoveState &moveState = pPartyRuntime->movementState();
    const float deltaX = target->x - moveState.x;
    const float deltaY = target->y - moveState.y;
    const float horizontalLengthSquared = deltaX * deltaX + deltaY * deltaY;

    if (horizontalLengthSquared <= 0.000001f)
    {
        return false;
    }

    view.setCameraAngles(std::atan2(deltaY, deltaX), view.cameraPitchRadians());
    return true;
}

bool OutdoorGameplayInputController::updateArpgModeOutdoorFrame(
    OutdoorGameView &view,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    if (!view.arpgModeEnabled() || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    view.syncGameplayMouseLookMode(SDL_GetMouseFocus(), false);
    view.updateArpgModeDelayedSpell(deltaSeconds);
    view.updateArpgModeLootAutoPickup(deltaSeconds);

    if (input.mouseWheelDelta != 0.0f)
    {
        view.m_gameSettings.arpgModeCameraDistance =
            std::clamp(
                view.m_gameSettings.arpgModeCameraDistance - input.mouseWheelDelta * ArpgModeCameraWheelStep,
                ArpgModeCameraMinDistance,
                ArpgModeCameraMaxDistance);
    }

    if (input.rightMouseButton.held)
    {
        if (!faceArpgModeNearestMeleeTarget(view))
        {
            faceArpgModePointerDirection(view, input);
        }
    }

    if (input.isScancodeHeld(SDL_SCANCODE_Q) && view.previousKeyboardState()[SDL_SCANCODE_Q] == 0)
    {
        faceArpgModePointerDirection(view, input);
    }

    const bool lootLabelActivated =
        input.leftMouseButton.pressed && view.tryActivateArpgModeLootLabelAt(input.pointerX, input.pointerY);

    if (lootLabelActivated)
    {
        view.m_arpgModeHasMoveDestination = false;
    }

    if (!lootLabelActivated && input.leftMouseButton.held)
    {
        const std::optional<bx::Vec3> destination = resolveArpgModeMoveClick(view, input);

        if (destination)
        {
            view.m_arpgModeHasMoveDestination = true;
            view.m_arpgModeMoveDestinationX = destination->x;
            view.m_arpgModeMoveDestinationY = destination->y;
            view.m_arpgModeMoveDestinationZ = destination->z;
        }
        else
        {
            view.m_arpgModeHasMoveDestination = false;
        }
    }

    const OutdoorMoveState moveState = view.m_pOutdoorPartyRuntime->movementState();
    const bool actionAnimationActive = view.m_arpgModeActionAnimationSeconds > 0.0f;
    float movementYawRadians = view.m_cameraYawRadians;
    float actualMovementYawRadians = movementYawRadians;
    bool hasActualMovementYaw = false;
    bool moveForward = false;

    if (!actionAnimationActive && view.m_arpgModeHasMoveDestination)
    {
        const float deltaX = view.m_arpgModeMoveDestinationX - moveState.x;
        const float deltaY = view.m_arpgModeMoveDestinationY - moveState.y;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY;
        const float stopRadius = std::max(4.0f, view.m_gameSettings.arpgModeClickStopRadius);

        if (distanceSquared <= stopRadius * stopRadius)
        {
            view.m_arpgModeHasMoveDestination = false;
        }
        else
        {
            movementYawRadians = std::atan2(deltaY, deltaX);
            view.m_cameraYawRadians = movementYawRadians;
            moveForward = true;
        }
    }

    if (view.m_pOutdoorSceneRuntime != nullptr)
    {
        view.m_pOutdoorPartyRuntime->setMovementSpeedMultiplier(view.m_gameSettings.arpgModeMoveSpeedMultiplier);

        const OutdoorMovementInput movementInput = {
            moveForward,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            movementYawRadians,
            0.0f,
            false
        };
        const OutdoorSceneRuntime::AdvanceFrameResult frameAdvanceResult =
            view.m_pOutdoorSceneRuntime->advanceFrame(movementInput, deltaSeconds);
        applyOutdoorFrameAdvanceResult(view, frameAdvanceResult);

        const OutdoorMoveState updatedMoveState = view.m_pOutdoorPartyRuntime->movementState();
        const float actualDeltaX = updatedMoveState.x - moveState.x;
        const float actualDeltaY = updatedMoveState.y - moveState.y;

        if (actualDeltaX * actualDeltaX + actualDeltaY * actualDeltaY > 0.0001f)
        {
            actualMovementYawRadians = std::atan2(actualDeltaY, actualDeltaX);
            hasActualMovementYaw = true;
        }
    }

    view.m_arpgModeMinimapArrowYawRadians = hasActualMovementYaw ? actualMovementYawRadians : view.m_cameraYawRadians;

    logArpgModeDirectionDiagnostic(
        moveForward,
        movementYawRadians,
        hasActualMovementYaw,
        actualMovementYawRadians,
        view.m_cameraYawRadians,
        view.m_arpgModeMinimapArrowYawRadians,
        deltaSeconds);

    if (view.m_arpgModeActionAnimationSeconds > 0.0f)
    {
        view.m_arpgModeActionAnimationElapsedSeconds += deltaSeconds;
        view.m_arpgModeActionAnimationSeconds = std::max(0.0f, view.m_arpgModeActionAnimationSeconds - deltaSeconds);
    }
    else
    {
        view.m_arpgModeActionAnimationDurationSeconds = 0.0f;
        view.m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    }

    const OutdoorMoveState &updatedMoveState = view.m_pOutdoorPartyRuntime->movementState();
    const float desiredCameraTargetX = updatedMoveState.x;
    const float desiredCameraTargetY = updatedMoveState.y;
    const float desiredCameraTargetZ = updatedMoveState.footZ + view.m_gameSettings.arpgModeCameraTargetHeight;
    const float cameraFollowLerp = std::max(0.0f, view.m_gameSettings.arpgModeCameraFollowLerp);
    const float cameraFollowAlpha =
        cameraFollowLerp <= 0.0f ? 1.0f : (1.0f - std::exp(-cameraFollowLerp * deltaSeconds));

    view.m_cameraTargetX += (desiredCameraTargetX - view.m_cameraTargetX) * cameraFollowAlpha;
    view.m_cameraTargetY += (desiredCameraTargetY - view.m_cameraTargetY) * cameraFollowAlpha;
    view.m_cameraTargetZ += (desiredCameraTargetZ - view.m_cameraTargetZ) * cameraFollowAlpha;
    return true;
}

void OutdoorGameplayInputController::updateCameraFromInput(
    OutdoorGameView &view,
    const GameplayInputFrame &input,
    float deltaSeconds)
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

    const bool arpgFirstPersonUseMode =
        view.m_gameSettings.arpgModeEnabled
        && view.arpgModeFirstPersonUseMode()
        && view.m_pOutdoorPartyRuntime != nullptr;

    if (arpgFirstPersonUseMode && !view.m_arpgModeFirstPersonUseModeActive)
    {
        view.m_arpgModeHasMoveDestination = false;
        view.m_cameraPitchRadians = 0.0f;
        view.m_isRotatingCamera = false;
    }

    view.m_arpgModeFirstPersonUseModeActive = arpgFirstPersonUseMode;

    if (sharedInputFrameResult.journalInputConsumed)
    {
        return;
    }

    if (sharedInputFrameResult.worldInputBlocked)
    {
        return;
    }

    if (updateArpgModeOutdoorFrame(view, input, deltaSeconds))
    {
        return;
    }

    const bool runWalkModifier = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL];
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
    const bool lookUpPressed = input.action(KeyboardAction::LookUp).held;
    const bool lookDownPressed = input.action(KeyboardAction::LookDown).held;
    const bool centerViewPressed = input.action(KeyboardAction::CenterView).held;

    const bool allowCameraMovementInput =
        !hasActiveLootView && !hasPendingSpellCast && !gameplayMouseLookState.cursorModeActive;
    const float keyboardYawSpeed = 1.75f;

    if (classicControls && allowCameraMovementInput)
    {
        if (leftPressed)
        {
            view.m_cameraYawRadians += keyboardYawSpeed * deltaSeconds;
        }

        if (rightPressed)
        {
            view.m_cameraYawRadians -= keyboardYawSpeed * deltaSeconds;
        }
    }

    if (view.m_outdoorMapData)
    {
        if (view.m_pOutdoorPartyRuntime)
        {
            if (allowCameraMovementInput)
            {
                const OutdoorMovementInput movementInput = {
                    moveForwardPressed,
                    moveBackwardPressed,
                    strafeLeftPressed,
                    strafeRightPressed,
                    jumpPressed,
                    flyUpPressed,
                    flyDownPressed,
                    runWalkModifier,
                    turboSpeed,
                    view.m_cameraYawRadians,
                    view.m_cameraPitchRadians,
                    !classicControls,
                    input.turnBasedMovementStep
                };
                if (view.m_pOutdoorSceneRuntime != nullptr)
                {
                    const OutdoorSceneRuntime::AdvanceFrameResult frameAdvanceResult =
                        view.m_pOutdoorSceneRuntime->advanceFrame(movementInput, deltaSeconds);
                    applyOutdoorFrameAdvanceResult(view, frameAdvanceResult);
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

    if (view.m_pOutdoorPartyRuntime)
    {
        if (input.action(KeyboardAction::Land).pressed && view.m_pOutdoorPartyRuntime->partyMovementState().flying)
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
