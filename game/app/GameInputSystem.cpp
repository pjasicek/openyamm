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
constexpr float MobileJoystickRadius = 64.0f;
constexpr float MobileJoystickDeadZone = 10.0f;
constexpr float MobileJoystickFullSpeedRadius = MobileJoystickRadius * 0.7f;
constexpr float MobileGameplayTapMaxNormalizedDistanceSquared = 0.000225f;
constexpr float MobileDebugConsoleGestureTopEdgeNormalized = 0.055f;
constexpr float MobileDebugConsoleGestureMinDragNormalized = 0.14f;
constexpr float MobileDebugConsoleGestureMaxHorizontalNormalized = 0.09f;
constexpr uint64_t MobileLongPressInspectNanoseconds = 400'000'000ULL;
constexpr uint64_t MobileInspectToggleNanoseconds = 650'000'000ULL;

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
#if !defined(__ANDROID__) && !defined(OPENYAMM_IOS)
    if ((event.type == SDL_EVENT_MOUSE_BUTTON_DOWN || event.type == SDL_EVENT_MOUSE_BUTTON_UP)
        && event.button.button >= SDL_BUTTON_LEFT && event.button.button <= SDL_BUTTON_RIGHT)
    {
        m_pendingMouseButtonEvents[event.button.button - SDL_BUTTON_LEFT].push_back(event.button);
        return;
    }
#endif

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

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    if (event.type == SDL_EVENT_MOUSE_MOTION && event.motion.which != SDL_TOUCH_MOUSEID)
    {
        m_mobilePointerPosition.reset();
    }

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
        pTouch->startTimestampNanoseconds = event.tfinger.timestamp;
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
            else if (pTouch->role == MobileTouchRole::Hud
                && pTouch->longPressCandidate
                && event.type == SDL_EVENT_FINGER_UP)
            {
                // A short tap on a long-press screen clicks only now that it has been released.
                m_mobilePendingHudTap = true;
                m_mobilePendingHudTapStartX = pTouch->startX;
                m_mobilePendingHudTapStartY = pTouch->startY;
                m_mobilePendingHudTapX = event.tfinger.x;
                m_mobilePendingHudTapY = event.tfinger.y;
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
    bool mobileInspectControlEnabled,
    bool mobileLongPressInspectEnabled,
    std::span<const GameplayTouchControl> touchControls)
{
    m_frame = {};
    m_frame.turboMovementEnabled = settings.turboMovementEnabled;
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

    const bool physicalLeftMouseButtonHeld = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const bool physicalRightMouseButtonHeld = (mouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool physicalMiddleMouseButtonHeld = (mouseButtons & SDL_BUTTON_MMASK) != 0;
    bool leftMouseButtonHeld = !blockGameplayInput && physicalLeftMouseButtonHeld;
    bool rightMouseButtonHeld = !blockGameplayInput && physicalRightMouseButtonHeld;
    bool middleMouseButtonHeld = !blockGameplayInput && physicalMiddleMouseButtonHeld;

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    if (m_mobilePointerPosition)
    {
        m_frame.pointerX = (*m_mobilePointerPosition)[0] * static_cast<float>(screenWidth);
        m_frame.pointerY = (*m_mobilePointerPosition)[1] * static_cast<float>(screenHeight);
    }
#endif

#if !defined(__ANDROID__) && !defined(OPENYAMM_IOS)
    // A quick click, such as a trackpad tap, can press and release between two frames, and the polled state then
    // misses it. Apply queued button events one per frame at their own positions: the UI derives clicks and drags
    // from the held state of consecutive frames.
    const auto applyPendingMouseButton =
        [this, blockGameplayInput](size_t buttonIndex, bool suppressed, bool &held)
        {
            std::deque<SDL_MouseButtonEvent> &events = m_pendingMouseButtonEvents[buttonIndex];

            if (blockGameplayInput || suppressed)
            {
                events.clear();
                return;
            }

            if (!events.empty())
            {
                const SDL_MouseButtonEvent event = events.front();
                events.pop_front();
                held = event.type == SDL_EVENT_MOUSE_BUTTON_DOWN;
                m_frame.pointerX = event.x;
                m_frame.pointerY = event.y;
            }
        };

    applyPendingMouseButton(0, m_suppressLeftMouseButtonUntilReleased, leftMouseButtonHeld);
    applyPendingMouseButton(1, m_suppressMiddleMouseButtonUntilReleased, middleMouseButtonHeld);
    applyPendingMouseButton(2, m_suppressRightMouseButtonUntilReleased, rightMouseButtonHeld);

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
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    m_frame.relativeMouseX = 0.0f;
    m_frame.relativeMouseY = 0.0f;
#else
    const float mouseSensitivityScale = static_cast<float>(std::clamp(settings.mouseSensitivity, 0, 100)) / 100.0f;
    m_frame.relativeMouseX = blockGameplayInput ? 0.0f : relativeMouseX * mouseSensitivityScale;
    m_frame.relativeMouseY = blockGameplayInput ? 0.0f
        : (settings.invertMouseY ? -relativeMouseY : relativeMouseY) * mouseSensitivityScale;
#endif

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
            if (binding.mouseButton == SDL_BUTTON_LEFT)
            {
                held = leftMouseButtonHeld;
            }
            else if (binding.mouseButton == SDL_BUTTON_RIGHT)
            {
                held = rightMouseButtonHeld;
            }
            else if (binding.mouseButton == SDL_BUTTON_MIDDLE)
            {
                held = middleMouseButtonHeld;
            }
            else
            {
                held = !blockGameplayInput && mouseButtonHeldInFlags(mouseButtons, binding.mouseButton);
            }
        }
        else if (binding.kind == InputBindingKind::MouseWheelUp)
        {
            held = m_frame.mouseWheelDelta > 0.0f;
        }
        else if (binding.kind == InputBindingKind::MouseWheelDown)
        {
            held = m_frame.mouseWheelDelta < 0.0f;
        }

        actionHeld[keyboardActionIndex(definition.action)] = held;
    }

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    const bool useMobileGameplayTouchControls = mobileGameplayTouchControlsEnabled && !blockGameplayInput;
    const bool useMobileJumpGesture = useMobileGameplayTouchControls && mobileJumpGestureEnabled;

    if (!mobileInspectControlEnabled || blockGameplayInput)
    {
        m_mobileInspectLocked = false;
    }

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
    // Drawing and touch capture use the same resolved YAML rectangles, including runtime party width.
    const auto controlAt = [touchControls, touchScale](float logicalX, float logicalY, GameplayTouchRole role)
    {
        return std::any_of(touchControls.begin(), touchControls.end(), [&](const GameplayTouchControl &control)
        {
            return control.role == role && control.contains(logicalX * touchScale, logicalY * touchScale);
        });
    };
    const auto touchStartsInHudZone =
        [&controlAt, &touchLogicalX, &touchLogicalY](float normalizedX, float normalizedY)
        {
            return controlAt(touchLogicalX(normalizedX), touchLogicalY(normalizedY), GameplayTouchRole::Hud);
        };
    const auto mobileInspectButtonAt = [&controlAt](float logicalX, float logicalY)
    {
        return controlAt(logicalX, logicalY, GameplayTouchRole::Inspect);
    };
    const auto mobileFlightControlAt =
        [&controlAt, mobileFlightControlsEnabled](float logicalX, float logicalY) -> MobileTouchRole
        {
            if (mobileFlightControlsEnabled)
            {
                if (controlAt(logicalX, logicalY, GameplayTouchRole::FlyUp))
                {
                    return MobileTouchRole::FlyUp;
                }
                if (controlAt(logicalX, logicalY, GameplayTouchRole::FlyDown))
                {
                    return MobileTouchRole::FlyDown;
                }
            }
            return MobileTouchRole::None;
        };

    bool inspectButtonHeld = false;
    bool longPressInspectHeld = false;
    bool inspectTargetPressed = false;
    float inspectTargetPressX = 0.0f;
    float inspectTargetPressY = 0.0f;
    const uint64_t nowNanoseconds = SDL_GetTicksNS();

    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        if (!touch.active)
        {
            continue;
        }

        // A still finger held on an inspectable overlay becomes the right button at that finger.
        if (!blockGameplayInput
            && mobileLongPressInspectEnabled
            && touch.role == MobileTouchRole::Hud
            && touch.longPressCandidate
            && !touch.dragThresholdExceeded
            && nowNanoseconds >= touch.startTimestampNanoseconds
            && nowNanoseconds - touch.startTimestampNanoseconds >= MobileLongPressInspectNanoseconds)
        {
            touch.role = MobileTouchRole::LongPressInspect;
        }

        if (touch.role == MobileTouchRole::LongPressInspect)
        {
            longPressInspectHeld = true;
        }

        if (!blockGameplayInput
            && mobileInspectControlEnabled
            && touch.role == MobileTouchRole::None
            && mobileInspectButtonAt(touchLogicalX(touch.startX), touchLogicalY(touch.startY)))
        {
            touch.role = MobileTouchRole::InspectModifier;
            touch.inspectToggleCandidate = true;
        }

        if (!blockGameplayInput
            && mobileInspectControlEnabled
            && touch.role == MobileTouchRole::InspectModifier)
        {
            inspectButtonHeld = true;
        }
    }

    if (inspectButtonHeld)
    {
        for (MobileTouchPoint &touch : m_mobileTouches)
        {
            if (!touch.active || touch.role != MobileTouchRole::InspectModifier || !touch.inspectToggleCandidate)
            {
                continue;
            }

            const bool hasOtherTouch = std::any_of(
                m_mobileTouches.begin(),
                m_mobileTouches.end(),
                [&touch](const MobileTouchPoint &other)
                {
                    return &other != &touch
                        && other.active
                        && other.role != MobileTouchRole::DebugConsoleGesture;
                });

            if (hasOtherTouch)
            {
                touch.inspectToggleCandidate = false;
                continue;
            }

            if (touch.startTimestampNanoseconds != 0
                && nowNanoseconds >= touch.startTimestampNanoseconds
                && nowNanoseconds - touch.startTimestampNanoseconds >= MobileInspectToggleNanoseconds)
            {
                m_mobileInspectLocked = !m_mobileInspectLocked;
                touch.inspectToggleCandidate = false;
            }
        }
    }

    m_frame.mobileInspectLocked = m_mobileInspectLocked;
    const bool inspectModifierHeld = inspectButtonHeld || m_mobileInspectLocked;

    if (inspectModifierHeld && m_mobilePendingHudTap)
    {
        inspectTargetPressed = true;
        inspectTargetPressX = m_mobilePendingHudTapX * static_cast<float>(screenWidth);
        inspectTargetPressY = m_mobilePendingHudTapY * static_cast<float>(screenHeight);
        m_mobilePendingHudTap = false;
        m_mobilePendingHudRelease = false;
    }

    if (inspectModifierHeld)
    {
        for (MobileTouchPoint &touch : m_mobileTouches)
        {
            if (touch.active
                && touch.role != MobileTouchRole::InspectModifier
                && touch.role != MobileTouchRole::DebugConsoleGesture)
            {
                if (!inspectTargetPressed && touch.role != MobileTouchRole::InspectTarget)
                {
                    inspectTargetPressed = true;
                    inspectTargetPressX = touch.x * static_cast<float>(screenWidth);
                    inspectTargetPressY = touch.y * static_cast<float>(screenHeight);
                }

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
            touch.longPressCandidate = mobileLongPressInspectEnabled && !blockGameplayInput;
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
    bool hasDeferredHudTouch = false;
    bool hasInspectTargetTouch = false;
    float hudTouchX = 0.0f;
    float hudTouchY = 0.0f;
    float deferredHudTouchX = 0.0f;
    float deferredHudTouchY = 0.0f;
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
        else if ((touch.role == MobileTouchRole::InspectTarget || touch.role == MobileTouchRole::LongPressInspect)
            && !hasInspectTargetTouch)
        {
            hasNonHudMobileTouch = true;
            hasInspectTargetTouch = true;
            inspectTargetX = touch.x * static_cast<float>(screenWidth);
            inspectTargetY = touch.y * static_cast<float>(screenHeight);
        }
        else if (touch.role == MobileTouchRole::Hud
            && touch.longPressCandidate
            && !touch.dragThresholdExceeded
            && !hasHudTouch
            && !hasDeferredHudTouch)
        {
            // Undecided between a tap (clicks on release) and a long press (inspects); only the pointer follows.
            hasDeferredHudTouch = true;
            deferredHudTouchX = touch.x * static_cast<float>(screenWidth);
            deferredHudTouchY = touch.y * static_cast<float>(screenHeight);
        }
        else if (touch.role == MobileTouchRole::Hud && !hasHudTouch)
        {
            hasHudTouch = true;
            // A deferred press reaches the item under the finger's start when its drag begins.
            const bool pressAtStart = touch.longPressCandidate && !touch.dragStartDelivered;
            hudTouchX = (pressAtStart ? touch.startX : touch.x) * static_cast<float>(screenWidth);
            hudTouchY = (pressAtStart ? touch.startY : touch.y) * static_cast<float>(screenHeight);

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
    const bool hasMobilePointerInput = inspectModifierHeld || longPressInspectHeld || hasHudTouch
        || hasDeferredHudTouch || pendingHudDragIsUiGesture || m_mobilePendingHudTap || m_mobilePendingHudRelease;

    if (inspectModifierHeld || longPressInspectHeld)
    {
        if (inspectTargetPressed)
        {
            m_frame.pointerX = inspectTargetPressX;
            m_frame.pointerY = inspectTargetPressY;
        }
        else if (hasInspectTargetTouch)
        {
            m_frame.pointerX = inspectTargetX;
            m_frame.pointerY = inspectTargetY;
        }

        leftMouseButtonHeld = false;
        rightMouseButtonHeld = true;
    }
    else if (pendingHudDragIsUiGesture)
    {
        m_frame.mobileTouchDragStartX = m_mobilePendingHudDragStartX * static_cast<float>(screenWidth);
        m_frame.mobileTouchDragStartY = m_mobilePendingHudDragStartY * static_cast<float>(screenHeight);
        if (!m_mobilePendingHudDragStartDelivered)
        {
            // Deliver the pickup before the drop even when the whole gesture fits between frames.
            m_frame.pointerX = m_frame.mobileTouchDragStartX;
            m_frame.pointerY = m_frame.mobileTouchDragStartY;
            m_frame.mobileTouchDragStarted = true;
            m_frame.mobileTouchDragActive = true;
            leftMouseButtonHeld = true;
            m_mobilePendingHudDragStartDelivered = true;
        }
        else
        {
            m_frame.pointerX = m_mobilePendingHudDragReleaseX * static_cast<float>(screenWidth);
            m_frame.pointerY = m_mobilePendingHudDragReleaseY * static_cast<float>(screenHeight);
            m_frame.mobileTouchDragReleased = true;
            leftMouseButtonHeld = false;
            m_mobilePendingHudDragRelease = false;
        }
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
    else if (hasDeferredHudTouch)
    {
        m_frame.pointerX = deferredHudTouchX;
        m_frame.pointerY = deferredHudTouchY;
        leftMouseButtonHeld = false;
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

    if (hasMobilePointerInput && screenWidth > 0 && screenHeight > 0)
    {
        m_mobilePointerPosition = std::array<float, 2>{
            m_frame.pointerX / static_cast<float>(screenWidth),
            m_frame.pointerY / static_cast<float>(screenHeight)};
    }
#else
    static_cast<void>(mobileGameplayTouchControlsEnabled);
    static_cast<void>(mobileJumpGestureEnabled);
    static_cast<void>(mobileFlightControlsEnabled);
    static_cast<void>(mobileInspectControlEnabled);
    static_cast<void>(mobileLongPressInspectEnabled);
    static_cast<void>(touchControls);
#endif

    m_frame.leftMouseButton = buildButtonState(leftMouseButtonHeld, m_previousLeftMouseButtonHeld);
    m_frame.rightMouseButton = buildButtonState(rightMouseButtonHeld, m_previousRightMouseButtonHeld);
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    if (inspectTargetPressed && rightMouseButtonHeld)
    {
        // A new target touch is a new right-click even while the magnifier keeps the button logically held.
        m_frame.rightMouseButton.pressed = true;
    }
#endif
    m_frame.middleMouseButton = buildButtonState(middleMouseButtonHeld, m_previousMiddleMouseButtonHeld);

    for (size_t actionIndex = 0; actionIndex < actionHeld.size(); ++actionIndex)
    {
        m_frame.actions[actionIndex] = buildButtonState(actionHeld[actionIndex], m_previousActionHeld[actionIndex]);
        const InputBindingKind kind = settings.keyboard.bindings[actionIndex].kind;
        if (kind == InputBindingKind::MouseWheelUp || kind == InputBindingKind::MouseWheelDown)
        {
            m_frame.actions[actionIndex].pressed = actionHeld[actionIndex];
        }
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

GameplayInputFrame &GameInputSystem::frame()
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
    m_mobileInspectLocked = false;

    for (MobileTouchPoint &touch : m_mobileTouches)
    {
        touch.inspectToggleCandidate = false;
    }
}
} // namespace OpenYAMM::Game
