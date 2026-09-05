#include "game/app/GameInputSystem.h"

#include "game/app/MobileJoystickDirection.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MobileLogicalHeight = 480.0f;
constexpr float MobileMovementZoneX = 0.0f;
constexpr float MobileMovementZoneY = 160.0f;
constexpr float MobileMovementZoneWidth = 300.0f;
constexpr float MobileMovementZoneHeight = 320.0f;
constexpr float MobileCameraZoneX = 300.0f;
constexpr float MobileFlightControlRightInset = 0.0f;
constexpr float MobileFlightControlTop = 160.0f;
constexpr float MobileFlightControlHeight = 64.0f;
constexpr float MobileFlightControlTouchWidth = 40.0f;
constexpr float MobileFlightControlTouchInset = 16.0f;
constexpr float MobileFlightControlTouchPanelWidth = 96.0f;
constexpr float MobileInspectButtonLeft = 20.0f;
constexpr float MobileInspectButtonTop = 296.0f;
constexpr float MobileInspectButtonWidth = 80.0f;
constexpr float MobileInspectButtonHeight = 80.0f;
constexpr float MobileJoystickRadius = 64.0f;
constexpr float MobileJoystickDeadZone = 10.0f;
constexpr float MobileJoystickFullSpeedRadius = MobileJoystickRadius * 0.7f;
constexpr float MobileGameplayTapMaxNormalizedDistanceSquared = 0.000225f;
constexpr float MobileDebugConsoleGestureTopEdgeNormalized = 0.055f;
constexpr float MobileDebugConsoleGestureMinDragNormalized = 0.14f;
constexpr float MobileDebugConsoleGestureMaxHorizontalNormalized = 0.09f;

GameplayButtonInputState buildButtonState(bool held, bool previousHeld)
{
    GameplayButtonInputState state = {};
    state.held = held;
    state.pressed = held && !previousHeld;
    state.released = !held && previousHeld;
    return state;
}

float mobileLogicalScale(int screenHeight)
{
    return screenHeight > 0 ? static_cast<float>(screenHeight) / MobileLogicalHeight : 1.0f;
}

bool pointInsideRect(float x, float y, float rectX, float rectY, float rectWidth, float rectHeight)
{
    return x >= rectX && y >= rectY && x <= rectX + rectWidth && y <= rectY + rectHeight;
}

void suppressButtonWhileHeld(bool physicalHeld, bool &logicalHeld, bool &suppressUntilReleased)
{
    if (!suppressUntilReleased)
    {
        return;
    }

    if (physicalHeld)
    {
        logicalHeld = false;
        return;
    }

    suppressUntilReleased = false;
}

} // namespace

void GameInputSystem::handleSdlEvent(const SDL_Event &event)
{
    if (isGamepadSdlEvent(event))
    {
        m_gamepadInput.handleSdlEvent(event);
        return;
    }

    if (event.type == SDL_EVENT_TEXT_INPUT)
    {
        if (event.text.text != nullptr)
        {
            m_pendingTextInput.append(event.text.text, std::strlen(event.text.text));
        }

        return;
    }

    if (event.type == SDL_EVENT_KEY_DOWN
        && !event.key.repeat
        && event.key.scancode > SDL_SCANCODE_UNKNOWN
        && event.key.scancode < SDL_SCANCODE_COUNT)
    {
        uint16_t &pressCount = m_pendingKeyboardPressCounts[event.key.scancode];

        if (pressCount < std::numeric_limits<uint16_t>::max())
        {
            ++pressCount;
        }
    }

#if defined(__ANDROID__)
    const auto findTouch =
        [this](SDL_FingerID fingerId) -> MobileTouchPoint *
        {
            for (MobileTouchPoint &touch : m_mobileTouches)
            {
                if (touch.active && touch.fingerId == fingerId)
                {
                    return &touch;
                }
            }

            return nullptr;
        };

    if (event.type == SDL_EVENT_FINGER_DOWN)
    {
        MobileTouchPoint *pTouch = findTouch(event.tfinger.fingerID);

        if (pTouch == nullptr)
        {
            for (MobileTouchPoint &candidate : m_mobileTouches)
            {
                if (!candidate.active)
                {
                    pTouch = &candidate;
                    break;
                }
            }
        }

        if (pTouch == nullptr)
        {
            return;
        }

        *pTouch = {};
        pTouch->active = true;
        pTouch->fingerId = event.tfinger.fingerID;
        pTouch->startX = event.tfinger.x;
        pTouch->startY = event.tfinger.y;
        pTouch->x = event.tfinger.x;
        pTouch->y = event.tfinger.y;
        pTouch->debugConsoleGestureCandidate =
            event.tfinger.y >= 0.0f && event.tfinger.y <= MobileDebugConsoleGestureTopEdgeNormalized;
        return;
    }

    if (event.type == SDL_EVENT_FINGER_MOTION)
    {
        MobileTouchPoint *pTouch = findTouch(event.tfinger.fingerID);

        if (pTouch == nullptr)
        {
            return;
        }

        pTouch->deltaX += event.tfinger.x - pTouch->x;
        pTouch->deltaY += event.tfinger.y - pTouch->y;
        pTouch->x = event.tfinger.x;
        pTouch->y = event.tfinger.y;

        const float touchDragX = pTouch->x - pTouch->startX;
        const float touchDragY = pTouch->y - pTouch->startY;
        pTouch->dragThresholdExceeded =
            pTouch->dragThresholdExceeded
            || touchDragX * touchDragX + touchDragY * touchDragY
                > MobileGameplayTapMaxNormalizedDistanceSquared;

        if (pTouch->debugConsoleGestureCandidate && !pTouch->debugConsoleGestureTriggered)
        {
            const float dragX = event.tfinger.x - pTouch->startX;
            const float dragY = event.tfinger.y - pTouch->startY;

            if (dragY >= MobileDebugConsoleGestureMinDragNormalized
                && std::abs(dragX) <= MobileDebugConsoleGestureMaxHorizontalNormalized)
            {
                pTouch->role = MobileTouchRole::DebugConsoleGesture;
                pTouch->debugConsoleGestureTriggered = true;
                pTouch->dragThresholdExceeded = false;
                m_mobilePendingHudTap = false;
                m_mobilePendingHudRelease = false;
                m_mobilePendingCameraTap = false;
                m_mobileJumpDoubleTapGesture.cancel();
                m_mobileDebugConsoleToggleRequested = true;
            }
        }

        return;
    }

    if (event.type == SDL_EVENT_FINGER_UP || event.type == SDL_EVENT_FINGER_CANCELED)
    {
        MobileTouchPoint *pTouch = findTouch(event.tfinger.fingerID);

        if (pTouch != nullptr)
        {
            const bool completedHudDrag =
                event.type == SDL_EVENT_FINGER_UP
                && pTouch->dragThresholdExceeded
                && (pTouch->role == MobileTouchRole::Hud || pTouch->role == MobileTouchRole::None);

            if (completedHudDrag)
            {
                m_mobilePendingHudDragRelease = true;
                m_mobilePendingHudDragStartDelivered = pTouch->dragStartDelivered;
                m_mobilePendingHudDragStartX = pTouch->startX;
                m_mobilePendingHudDragStartY = pTouch->startY;
                m_mobilePendingHudDragReleaseX = event.tfinger.x;
                m_mobilePendingHudDragReleaseY = event.tfinger.y;
                m_mobilePendingHudRelease = false;
                m_mobilePendingHudTap = false;
            }
            else if (pTouch->role == MobileTouchRole::Hud)
            {
                m_mobilePendingHudRelease = true;
                m_mobilePendingHudReleaseX = event.tfinger.x;
                m_mobilePendingHudReleaseY = event.tfinger.y;
            }
            else if (pTouch->role == MobileTouchRole::Camera)
            {
                const float deltaX = event.tfinger.x - pTouch->startX;
                const float deltaY = event.tfinger.y - pTouch->startY;
                const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

                if (event.type == SDL_EVENT_FINGER_UP
                    && !pTouch->dragThresholdExceeded
                    && distanceSquared <= MobileGameplayTapMaxNormalizedDistanceSquared)
                {
                    m_mobilePendingCameraTap = true;
                    m_mobilePendingCameraTapTimestampNanoseconds = event.tfinger.timestamp;
                    m_mobilePendingCameraTapX = event.tfinger.x;
                    m_mobilePendingCameraTapY = event.tfinger.y;
                }
            }
            else if (pTouch->role == MobileTouchRole::None)
            {
                m_mobilePendingHudTap = true;
                m_mobilePendingHudTapStartX = pTouch->startX;
                m_mobilePendingHudTapStartY = pTouch->startY;
                m_mobilePendingHudTapX = event.tfinger.x;
                m_mobilePendingHudTapY = event.tfinger.y;
            }

            *pTouch = {};
        }
    }
#else
    (void)event;
#endif
}

bool GameInputSystem::consumeMobileDebugConsoleToggleRequested()
{
    const bool requested = m_mobileDebugConsoleToggleRequested;
    m_mobileDebugConsoleToggleRequested = false;
    return requested;
}

void GameInputSystem::updateFromEngineInput(
    int screenWidth,
    int screenHeight,
    float mouseWheelDelta,
    const GameSettings &settings,
    bool blockGameplayInput,
    bool mobileGameplayTouchControlsEnabled,
    bool mobileJumpGestureEnabled,
    bool mobileFlightControlsEnabled,
    bool mobileInspectControlEnabled)
{
    m_frame = {};
    m_frame.screenWidth = screenWidth;
    m_frame.screenHeight = screenHeight;
    m_frame.mouseWheelDelta = blockGameplayInput ? 0.0f : mouseWheelDelta;
    m_frame.textInput = blockGameplayInput ? std::string() : std::move(m_pendingTextInput);
    m_pendingTextInput.clear();

    if (!blockGameplayInput)
    {
        m_frame.keyboardPressCounts = m_pendingKeyboardPressCounts;
    }

    m_pendingKeyboardPressCounts.fill(0);

    int keyboardStateCount = 0;
    const bool *pKeyboardState = SDL_GetKeyboardState(&keyboardStateCount);

    if (pKeyboardState != nullptr)
    {
        for (int scancode = 0; scancode < keyboardStateCount && scancode < SDL_SCANCODE_COUNT; ++scancode)
        {
            m_frame.keyboardHeld[scancode] = blockGameplayInput ? false : pKeyboardState[scancode];
        }
    }

    float pointerX = 0.0f;
    float pointerY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&pointerX, &pointerY);
    m_frame.pointerX = pointerX;
    m_frame.pointerY = pointerY;

#if !defined(__ANDROID__)
    SDL_Window *pMouseLookWindow = SDL_GetMouseFocus();

    if (pMouseLookWindow == nullptr)
    {
        pMouseLookWindow = SDL_GetKeyboardFocus();
    }

    if (settings.controlScheme == ControlScheme::Modern
        && pMouseLookWindow != nullptr
        && SDL_GetWindowRelativeMouseMode(pMouseLookWindow)
        && screenWidth > 0
        && screenHeight > 0)
    {
        m_frame.pointerX = static_cast<float>(screenWidth) * 0.5f;
        m_frame.pointerY = static_cast<float>(screenHeight) * 0.5f;
    }
#endif

    float relativeMouseX = 0.0f;
    float relativeMouseY = 0.0f;
    SDL_GetRelativeMouseState(&relativeMouseX, &relativeMouseY);
#if defined(__ANDROID__)
    m_frame.relativeMouseX = 0.0f;
    m_frame.relativeMouseY = 0.0f;
#else
    const float mouseSensitivityScale = static_cast<float>(std::clamp(settings.mouseSensitivity, 0, 100)) / 100.0f;
    m_frame.relativeMouseX = blockGameplayInput ? 0.0f : relativeMouseX * mouseSensitivityScale;
    m_frame.relativeMouseY = blockGameplayInput ? 0.0f : relativeMouseY * mouseSensitivityScale;
#endif

    const bool physicalLeftMouseButtonHeld = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const bool physicalRightMouseButtonHeld = (mouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool physicalMiddleMouseButtonHeld = (mouseButtons & SDL_BUTTON_MMASK) != 0;
    bool leftMouseButtonHeld = !blockGameplayInput && physicalLeftMouseButtonHeld;
    bool rightMouseButtonHeld = !blockGameplayInput && physicalRightMouseButtonHeld;
    bool middleMouseButtonHeld = !blockGameplayInput && physicalMiddleMouseButtonHeld;

    suppressButtonWhileHeld(
        physicalLeftMouseButtonHeld,
        leftMouseButtonHeld,
        m_suppressLeftMouseButtonUntilReleased);
    suppressButtonWhileHeld(
        physicalRightMouseButtonHeld,
        rightMouseButtonHeld,
        m_suppressRightMouseButtonUntilReleased);
    suppressButtonWhileHeld(
        physicalMiddleMouseButtonHeld,
        middleMouseButtonHeld,
        m_suppressMiddleMouseButtonUntilReleased);

    std::array<bool, KeyboardActionCount> actionHeld = {};

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        const InputBinding binding = settings.keyboard.binding(definition.action);
        bool held = false;

        if (binding.kind == InputBindingKind::Keyboard)
        {
            held =
                binding.scancode > SDL_SCANCODE_UNKNOWN
                && binding.scancode < SDL_SCANCODE_COUNT
                && m_frame.keyboardHeld[binding.scancode];
        }
        else if (binding.kind == InputBindingKind::MouseButton)
        {
            held =
                (binding.mouseButton == SDL_BUTTON_LEFT && leftMouseButtonHeld)
                || (binding.mouseButton == SDL_BUTTON_RIGHT && rightMouseButtonHeld)
                || (binding.mouseButton == SDL_BUTTON_MIDDLE && middleMouseButtonHeld);
        }

        actionHeld[keyboardActionIndex(definition.action)] = held;
    }

#if defined(__ANDROID__)
    const bool useMobileGameplayTouchControls = mobileGameplayTouchControlsEnabled && !blockGameplayInput;
    const bool useMobileJumpGesture = useMobileGameplayTouchControls && mobileJumpGestureEnabled;
    const auto setMobileActionHeld =
        [&settings, &actionHeld, this](KeyboardAction action)
        {
            actionHeld[keyboardActionIndex(action)] = true;

            const SDL_Scancode scancode = settings.keyboard.keyboardBinding(action);
            if (scancode > SDL_SCANCODE_UNKNOWN && scancode < SDL_SCANCODE_COUNT)
            {
                m_frame.keyboardHeld[scancode] = true;
            }
        };
    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        if (!mobileFlightControlsEnabled
            && (touch.role == MobileTouchRole::FlyUp || touch.role == MobileTouchRole::FlyDown))
        {
            touch.role = MobileTouchRole::None;
            touch.startX = touch.x;
            touch.startY = touch.y;
            touch.deltaX = 0.0f;
            touch.deltaY = 0.0f;
        }

    }

    const float touchScale = mobileLogicalScale(screenHeight);
    const float logicalWidth = touchScale > 0.0f ? static_cast<float>(screenWidth) / touchScale : 0.0f;
    const auto touchLogicalX =
        [screenWidth, touchScale](float normalizedX) -> float
        {
            return touchScale > 0.0f ? normalizedX * static_cast<float>(screenWidth) / touchScale : 0.0f;
        };
    const auto touchLogicalY =
        [screenHeight, touchScale](float normalizedY) -> float
        {
            return touchScale > 0.0f ? normalizedY * static_cast<float>(screenHeight) / touchScale : 0.0f;
        };
    const auto touchStartsInHudZone =
        [logicalWidth, &touchLogicalX, &touchLogicalY](float normalizedX, float normalizedY) -> bool
        {
            const float startLogicalX = touchLogicalX(normalizedX);
            const float startLogicalY = touchLogicalY(normalizedY);
            return pointInsideRect(startLogicalX, startLogicalY, 0.0f, 0.0f, 562.0f, 120.0f)
                || pointInsideRect(startLogicalX, startLogicalY, logicalWidth - 180.0f, 0.0f, 180.0f, 170.0f)
                || pointInsideRect(startLogicalX, startLogicalY, 0.0f, 376.0f, 210.0f, 104.0f)
                || pointInsideRect(
                    startLogicalX,
                    startLogicalY,
                    logicalWidth - 268.0f,
                    416.0f,
                    260.0f,
                    56.0f)
                || pointInsideRect(startLogicalX, startLogicalY, logicalWidth - 236.0f, 284.0f, 236.0f, 128.0f)
                || pointInsideRect(startLogicalX, startLogicalY, 320.0f, 360.0f, 420.0f, 120.0f);
        };
    const auto mobileInspectButtonAt =
        [](float logicalX, float logicalY) -> bool
        {
            return pointInsideRect(
                logicalX,
                logicalY,
                MobileInspectButtonLeft,
                MobileInspectButtonTop,
                MobileInspectButtonWidth,
                MobileInspectButtonHeight);
        };
    const auto mobileFlightControlAt =
        [logicalWidth, mobileFlightControlsEnabled](float logicalX, float logicalY) -> MobileTouchRole
        {
            if (!mobileFlightControlsEnabled)
            {
                return MobileTouchRole::None;
            }

            const float panelX =
                logicalWidth - MobileFlightControlRightInset - MobileFlightControlTouchPanelWidth;

            if (pointInsideRect(
                    logicalX,
                    logicalY,
                    panelX + MobileFlightControlTouchInset,
                    MobileFlightControlTop,
                    MobileFlightControlTouchWidth,
                    MobileFlightControlHeight))
            {
                return MobileTouchRole::FlyUp;
            }

            const float flyDownX =
                panelX + MobileFlightControlTouchInset + MobileFlightControlTouchWidth;

            if (pointInsideRect(
                    logicalX,
                    logicalY,
                    flyDownX,
                    MobileFlightControlTop,
                    MobileFlightControlTouchWidth,
                    MobileFlightControlHeight))
            {
                return MobileTouchRole::FlyDown;
            }

            return MobileTouchRole::None;
        };

    bool inspectModifierHeld = false;

    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        if (!touch.active)
        {
            continue;
        }

        if (!blockGameplayInput
            && mobileInspectControlEnabled
            && touch.role == MobileTouchRole::None
            && mobileInspectButtonAt(touchLogicalX(touch.startX), touchLogicalY(touch.startY)))
        {
            touch.role = MobileTouchRole::InspectModifier;
        }

        if (!blockGameplayInput
            && mobileInspectControlEnabled
            && touch.role == MobileTouchRole::InspectModifier)
        {
            inspectModifierHeld = true;
        }
    }

    if (inspectModifierHeld)
    {
        for (MobileTouchPoint &touch : m_mobileTouches)
        {
            if (touch.active
                && touch.role != MobileTouchRole::InspectModifier
                && touch.role != MobileTouchRole::DebugConsoleGesture)
            {
                touch.role = MobileTouchRole::InspectTarget;
            }
        }

        m_mobilePendingHudTap = false;
        m_mobilePendingHudRelease = false;
        m_mobilePendingHudDragRelease = false;
        m_mobilePendingCameraTap = false;
        m_mobileJumpDoubleTapGesture.cancel();
    }

    bool hasMovementTouch = false;
    bool hasCameraTouch = false;

    for (const MobileTouchPoint &touch : m_mobileTouches)
    {
        if (touch.active && touch.role == MobileTouchRole::Movement)
        {
            hasMovementTouch = true;
        }
        else if (touch.active && touch.role == MobileTouchRole::Camera)
        {
            hasCameraTouch = true;
        }
    }

    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        if (!touch.active || touch.role != MobileTouchRole::None)
        {
            continue;
        }

        const float startLogicalX = touchLogicalX(touch.startX);
        const float startLogicalY = touchLogicalY(touch.startY);
        const bool startsInMovementZone = pointInsideRect(
            startLogicalX,
            startLogicalY,
            MobileMovementZoneX,
            MobileMovementZoneY,
            MobileMovementZoneWidth,
            MobileMovementZoneHeight);
        const bool startsInHudZone = touchStartsInHudZone(touch.startX, touch.startY);
        const bool startsInCameraZone = startLogicalX >= MobileCameraZoneX;
        const MobileTouchRole flightControl = mobileFlightControlAt(startLogicalX, startLogicalY);

        if (!useMobileGameplayTouchControls)
        {
            touch.role = MobileTouchRole::Hud;
        }
        else if (flightControl != MobileTouchRole::None)
        {
            touch.role = flightControl;
        }
        else if (startsInHudZone)
        {
            touch.role = MobileTouchRole::Hud;
        }
        else if (startsInMovementZone && !hasMovementTouch)
        {
            touch.role = MobileTouchRole::Movement;
            hasMovementTouch = true;
        }
        else if (startsInCameraZone && !hasCameraTouch)
        {
            touch.role = MobileTouchRole::Camera;
            hasCameraTouch = true;
        }
        else
        {
            touch.role = MobileTouchRole::Hud;
        }

    }

    bool hasNonHudMobileTouch = false;
    bool hasHudTouch = false;
    bool hasInspectTargetTouch = false;
    float hudTouchX = 0.0f;
    float hudTouchY = 0.0f;
    float inspectTargetX = 0.0f;
    float inspectTargetY = 0.0f;

    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        if (!touch.active)
        {
            continue;
        }

        if (touch.role == MobileTouchRole::FlyUp || touch.role == MobileTouchRole::FlyDown)
        {
            hasNonHudMobileTouch = true;

            if (useMobileGameplayTouchControls && mobileFlightControlsEnabled)
            {
                setMobileActionHeld(
                    touch.role == MobileTouchRole::FlyUp ? KeyboardAction::FlyUp : KeyboardAction::FlyDown);
            }
        }
        else if (touch.role == MobileTouchRole::Movement)
        {
            hasNonHudMobileTouch = true;
            const float startX = touch.startX * static_cast<float>(screenWidth);
            const float startY = touch.startY * static_cast<float>(screenHeight);
            const float deltaLogicalX = touchLogicalX(touch.x) - touchLogicalX(touch.startX);
            const float deltaLogicalY = touchLogicalY(touch.y) - touchLogicalY(touch.startY);
            const float distance = std::sqrt(deltaLogicalX * deltaLogicalX + deltaLogicalY * deltaLogicalY);
            const float clampedDistance = std::min(distance, MobileJoystickRadius);
            float clampedLogicalX = 0.0f;
            float clampedLogicalY = 0.0f;

            if (distance > 0.001f)
            {
                clampedLogicalX = deltaLogicalX * clampedDistance / distance;
                clampedLogicalY = deltaLogicalY * clampedDistance / distance;
            }

            m_frame.mobileJoystickActive = true;
            m_frame.mobileJoystickBaseX = startX;
            m_frame.mobileJoystickBaseY = startY;
            m_frame.mobileJoystickKnobX = startX + clampedLogicalX * touchScale;
            m_frame.mobileJoystickKnobY = startY + clampedLogicalY * touchScale;
            m_frame.movementSpeedScale = mobileJoystickMovementSpeedScale(
                deltaLogicalX,
                deltaLogicalY,
                MobileJoystickDeadZone,
                MobileJoystickFullSpeedRadius);

            const MobileJoystickDirection joystickDirection = quantizeMobileJoystickDirection(
                deltaLogicalX,
                deltaLogicalY,
                MobileJoystickDeadZone);

            switch (joystickDirection)
            {
                case MobileJoystickDirection::North:
                    setMobileActionHeld(KeyboardAction::Forward);
                    break;
                case MobileJoystickDirection::NorthEast:
                    setMobileActionHeld(KeyboardAction::Forward);
                    setMobileActionHeld(KeyboardAction::Right);
                    break;
                case MobileJoystickDirection::East:
                    setMobileActionHeld(KeyboardAction::Right);
                    break;
                case MobileJoystickDirection::SouthEast:
                    setMobileActionHeld(KeyboardAction::Backward);
                    setMobileActionHeld(KeyboardAction::Right);
                    break;
                case MobileJoystickDirection::South:
                    setMobileActionHeld(KeyboardAction::Backward);
                    break;
                case MobileJoystickDirection::SouthWest:
                    setMobileActionHeld(KeyboardAction::Backward);
                    setMobileActionHeld(KeyboardAction::Left);
                    break;
                case MobileJoystickDirection::West:
                    setMobileActionHeld(KeyboardAction::Left);
                    break;
                case MobileJoystickDirection::NorthWest:
                    setMobileActionHeld(KeyboardAction::Forward);
                    setMobileActionHeld(KeyboardAction::Left);
                    break;
                case MobileJoystickDirection::Neutral:
                    break;
            }
        }
        else if (touch.role == MobileTouchRole::Camera)
        {
            hasNonHudMobileTouch = true;
            m_frame.relativeMouseX += touch.deltaX * static_cast<float>(screenWidth);
            m_frame.relativeMouseY += touch.deltaY * static_cast<float>(screenHeight);

            if (touch.dragThresholdExceeded)
            {
                m_mobileJumpDoubleTapGesture.cancel();
            }
        }
        else if (touch.role == MobileTouchRole::InspectModifier)
        {
            hasNonHudMobileTouch = true;
        }
        else if (touch.role == MobileTouchRole::InspectTarget && !hasInspectTargetTouch)
        {
            hasNonHudMobileTouch = true;
            hasInspectTargetTouch = true;
            inspectTargetX = touch.x * static_cast<float>(screenWidth);
            inspectTargetY = touch.y * static_cast<float>(screenHeight);
        }
        else if (touch.role == MobileTouchRole::Hud && !hasHudTouch)
        {
            hasHudTouch = true;
            hudTouchX = touch.x * static_cast<float>(screenWidth);
            hudTouchY = touch.y * static_cast<float>(screenHeight);

            if (touch.dragThresholdExceeded)
            {
                m_frame.mobileTouchDragActive = true;
                m_frame.mobileTouchDragStartX = touch.startX * static_cast<float>(screenWidth);
                m_frame.mobileTouchDragStartY = touch.startY * static_cast<float>(screenHeight);

                if (!touch.dragStartDelivered)
                {
                    m_frame.mobileTouchDragStarted = true;
                    touch.dragStartDelivered = true;
                }
            }
        }
        else if (touch.role == MobileTouchRole::DebugConsoleGesture)
        {
            hasNonHudMobileTouch = true;
        }

        touch.deltaX = 0.0f;
        touch.deltaY = 0.0f;
    }

    const bool pendingHudDragIsUiGesture =
        m_mobilePendingHudDragRelease
        && (!useMobileGameplayTouchControls
            || touchStartsInHudZone(m_mobilePendingHudDragStartX, m_mobilePendingHudDragStartY));

    if (inspectModifierHeld)
    {
        if (hasInspectTargetTouch)
        {
            m_frame.pointerX = inspectTargetX;
            m_frame.pointerY = inspectTargetY;
        }

        leftMouseButtonHeld = false;
        rightMouseButtonHeld = true;
    }
    else if (pendingHudDragIsUiGesture)
    {
        m_frame.pointerX = m_mobilePendingHudDragReleaseX * static_cast<float>(screenWidth);
        m_frame.pointerY = m_mobilePendingHudDragReleaseY * static_cast<float>(screenHeight);
        m_frame.mobileTouchDragStarted = !m_mobilePendingHudDragStartDelivered;
        m_frame.mobileTouchDragReleased = true;
        m_frame.mobileTouchDragStartX = m_mobilePendingHudDragStartX * static_cast<float>(screenWidth);
        m_frame.mobileTouchDragStartY = m_mobilePendingHudDragStartY * static_cast<float>(screenHeight);
        leftMouseButtonHeld = false;
        m_mobilePendingHudDragRelease = false;
    }
    else if (m_mobilePendingHudDragRelease)
    {
        m_mobilePendingHudDragRelease = false;
    }
    else if (hasHudTouch)
    {
        m_frame.pointerX = hudTouchX;
        m_frame.pointerY = hudTouchY;
        leftMouseButtonHeld = true;
        m_mobilePendingHudRelease = false;
    }
    else if (m_mobilePendingHudTap)
    {
        if (!useMobileGameplayTouchControls
            || touchStartsInHudZone(m_mobilePendingHudTapStartX, m_mobilePendingHudTapStartY))
        {
            m_frame.pointerX = m_mobilePendingHudTapX * static_cast<float>(screenWidth);
            m_frame.pointerY = m_mobilePendingHudTapY * static_cast<float>(screenHeight);
            leftMouseButtonHeld = true;
            m_mobilePendingHudRelease = true;
            m_mobilePendingHudReleaseX = m_mobilePendingHudTapX;
            m_mobilePendingHudReleaseY = m_mobilePendingHudTapY;
        }

        m_mobilePendingHudTap = false;
    }
    else if (m_mobilePendingHudRelease)
    {
        m_frame.pointerX = m_mobilePendingHudReleaseX * static_cast<float>(screenWidth);
        m_frame.pointerY = m_mobilePendingHudReleaseY * static_cast<float>(screenHeight);
        leftMouseButtonHeld = false;
        m_mobilePendingHudRelease = false;
    }
    else if (m_mobilePendingCameraTap)
    {
        if (useMobileJumpGesture)
        {
            const float logicalX = touchLogicalX(m_mobilePendingCameraTapX);
            const float logicalY = touchLogicalY(m_mobilePendingCameraTapY);

            if (m_mobileJumpDoubleTapGesture.registerCameraTap(
                    m_mobilePendingCameraTapTimestampNanoseconds,
                    logicalX,
                    logicalY))
            {
                setMobileActionHeld(KeyboardAction::Jump);
            }
        }

        m_mobilePendingCameraTap = false;
    }

    if (!useMobileJumpGesture)
    {
        m_mobilePendingCameraTap = false;
        m_mobileJumpDoubleTapGesture.cancel();
    }

    if (hasNonHudMobileTouch && !hasHudTouch)
    {
        leftMouseButtonHeld = false;
    }
#else
    static_cast<void>(mobileGameplayTouchControlsEnabled);
    static_cast<void>(mobileJumpGestureEnabled);
    static_cast<void>(mobileFlightControlsEnabled);
    static_cast<void>(mobileInspectControlEnabled);
#endif

    // Gamepad rides the same action and mouse-look paths as the keyboard and mouse.
    const uint64_t gamepadFrameTickNanoseconds = SDL_GetTicksNS();
    float gamepadDeltaSeconds = 1.0f / 60.0f;

    if (m_lastGamepadFrameTickNanoseconds != 0 && gamepadFrameTickNanoseconds > m_lastGamepadFrameTickNanoseconds)
    {
        gamepadDeltaSeconds = std::min(
            static_cast<float>(gamepadFrameTickNanoseconds - m_lastGamepadFrameTickNanoseconds) / 1000000000.0f,
            0.1f);
    }

    m_lastGamepadFrameTickNanoseconds = gamepadFrameTickNanoseconds;

    if (!blockGameplayInput)
    {
        SDL_Window *pGamepadWindow = SDL_GetMouseFocus();

        if (pGamepadWindow == nullptr)
        {
            pGamepadWindow = SDL_GetKeyboardFocus();
        }

        // The cursor is free whenever gameplay mouse-look is not capturing it (desktop) or the HUD
        // is showing something other than plain gameplay (Android). Then the pad drives the pointer.
#if defined(__ANDROID__)
        const bool gamepadCursorMode = !mobileGameplayTouchControlsEnabled;
#else
        const bool gamepadCursorMode =
            pGamepadWindow == nullptr || !SDL_GetWindowRelativeMouseMode(pGamepadWindow);
#endif

        const GamepadFrameResult gamepad =
            mapGamepadFrame(m_gamepadInput.state(), settings.gamepad, gamepadDeltaSeconds, gamepadCursorMode);

        if (gamepadCursorMode)
        {
            if ((gamepad.cursorDeltaX != 0.0f || gamepad.cursorDeltaY != 0.0f) && screenWidth > 0 && screenHeight > 0)
            {
                const float cursorX =
                    std::clamp(m_frame.pointerX + gamepad.cursorDeltaX, 0.0f, static_cast<float>(screenWidth - 1));
                const float cursorY =
                    std::clamp(m_frame.pointerY + gamepad.cursorDeltaY, 0.0f, static_cast<float>(screenHeight - 1));
                m_frame.pointerX = cursorX;
                m_frame.pointerY = cursorY;

                if (pGamepadWindow != nullptr)
                {
                    SDL_WarpMouseInWindow(pGamepadWindow, cursorX, cursorY);
                }
            }

            leftMouseButtonHeld = leftMouseButtonHeld || gamepad.cursorLeftHeld;
            rightMouseButtonHeld = rightMouseButtonHeld || gamepad.cursorRightHeld;
        }

        if (gamepad.escapeHeld)
        {
            m_frame.keyboardHeld[SDL_SCANCODE_ESCAPE] = true;

            if (!m_previousGamepadEscapeHeld)
            {
                ++m_frame.keyboardPressCounts[SDL_SCANCODE_ESCAPE];
            }
        }

        m_previousGamepadEscapeHeld = gamepad.escapeHeld;

        for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
        {
            const size_t actionIndex = keyboardActionIndex(definition.action);

            if (!gamepad.actionHeld[actionIndex])
            {
                continue;
            }

            actionHeld[actionIndex] = true;

            const SDL_Scancode scancode = settings.keyboard.keyboardBinding(definition.action);
            if (scancode > SDL_SCANCODE_UNKNOWN && scancode < SDL_SCANCODE_COUNT)
            {
                m_frame.keyboardHeld[scancode] = true;
            }
        }

        m_frame.relativeMouseX += gamepad.lookDeltaX;
        m_frame.relativeMouseY += gamepad.lookDeltaY;
    }

    m_frame.leftMouseButton = buildButtonState(leftMouseButtonHeld, m_previousLeftMouseButtonHeld);
    m_frame.rightMouseButton = buildButtonState(rightMouseButtonHeld, m_previousRightMouseButtonHeld);
    m_frame.middleMouseButton = buildButtonState(middleMouseButtonHeld, m_previousMiddleMouseButtonHeld);

    for (size_t actionIndex = 0; actionIndex < actionHeld.size(); ++actionIndex)
    {
        m_frame.actions[actionIndex] = buildButtonState(actionHeld[actionIndex], m_previousActionHeld[actionIndex]);
    }

    m_previousKeyboardHeld = m_frame.keyboardHeld;
    m_previousActionHeld = actionHeld;
    m_previousLeftMouseButtonHeld = leftMouseButtonHeld;
    m_previousRightMouseButtonHeld = rightMouseButtonHeld;
    m_previousMiddleMouseButtonHeld = middleMouseButtonHeld;
}

const GameplayInputFrame &GameInputSystem::frame() const
{
    return m_frame;
}

void GameInputSystem::resetRelativeMouseMotion()
{
    SDL_GetRelativeMouseState(nullptr, nullptr);
    m_frame.relativeMouseX = 0.0f;
    m_frame.relativeMouseY = 0.0f;
}

void GameInputSystem::suppressMouseButtonsUntilReleased()
{
    m_suppressLeftMouseButtonUntilReleased = true;
    m_suppressRightMouseButtonUntilReleased = true;
    m_suppressMiddleMouseButtonUntilReleased = true;
    m_previousLeftMouseButtonHeld = false;
    m_previousRightMouseButtonHeld = false;
    m_previousMiddleMouseButtonHeld = false;
}
} // namespace OpenYAMM::Game
