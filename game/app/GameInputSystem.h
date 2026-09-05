#pragma once

#include "game/app/GamepadInput.h"
#include "game/app/GameSettings.h"
#include "game/app/MobileJumpDoubleTapGesture.h"
#include "game/gameplay/GameplayInputFrame.h"

#include <array>
#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class GameInputSystem
{
public:
    void handleSdlEvent(const SDL_Event &event);

    void updateFromEngineInput(
        int screenWidth,
        int screenHeight,
        float mouseWheelDelta,
        const GameSettings &settings,
        bool blockGameplayInput = false,
        bool mobileGameplayTouchControlsEnabled = true,
        bool mobileJumpGestureEnabled = true,
        bool mobileFlightControlsEnabled = false,
        bool mobileInspectControlEnabled = true);

    const GameplayInputFrame &frame() const;
    bool consumeMobileDebugConsoleToggleRequested();
    void resetRelativeMouseMotion();
    void suppressMouseButtonsUntilReleased();

private:
    enum class MobileTouchRole
    {
        None,
        Movement,
        Camera,
        FlyUp,
        FlyDown,
        InspectModifier,
        InspectTarget,
        Hud,
        DebugConsoleGesture
    };

    struct MobileTouchPoint
    {
        bool active = false;
        SDL_FingerID fingerId = 0;
        MobileTouchRole role = MobileTouchRole::None;
        float startX = 0.0f;
        float startY = 0.0f;
        float x = 0.0f;
        float y = 0.0f;
        float deltaX = 0.0f;
        float deltaY = 0.0f;
        bool dragThresholdExceeded = false;
        bool dragStartDelivered = false;
        bool debugConsoleGestureCandidate = false;
        bool debugConsoleGestureTriggered = false;
    };

    GameplayInputFrame m_frame = {};
    GamepadInput m_gamepadInput;
    uint64_t m_lastGamepadFrameTickNanoseconds = 0;
    bool m_previousGamepadEscapeHeld = false;
    std::string m_pendingTextInput;
    std::array<uint16_t, SDL_SCANCODE_COUNT> m_pendingKeyboardPressCounts = {};
    std::array<bool, SDL_SCANCODE_COUNT> m_previousKeyboardHeld = {};
    std::array<bool, KeyboardActionCount> m_previousActionHeld = {};
    std::array<MobileTouchPoint, 8> m_mobileTouches = {};
    bool m_mobilePendingHudTap = false;
    float m_mobilePendingHudTapStartX = 0.0f;
    float m_mobilePendingHudTapStartY = 0.0f;
    float m_mobilePendingHudTapX = 0.0f;
    float m_mobilePendingHudTapY = 0.0f;
    bool m_mobilePendingHudRelease = false;
    float m_mobilePendingHudReleaseX = 0.0f;
    float m_mobilePendingHudReleaseY = 0.0f;
    bool m_mobilePendingHudDragRelease = false;
    bool m_mobilePendingHudDragStartDelivered = false;
    float m_mobilePendingHudDragStartX = 0.0f;
    float m_mobilePendingHudDragStartY = 0.0f;
    float m_mobilePendingHudDragReleaseX = 0.0f;
    float m_mobilePendingHudDragReleaseY = 0.0f;
    bool m_mobilePendingCameraTap = false;
    uint64_t m_mobilePendingCameraTapTimestampNanoseconds = 0;
    float m_mobilePendingCameraTapX = 0.0f;
    float m_mobilePendingCameraTapY = 0.0f;
    MobileJumpDoubleTapGesture m_mobileJumpDoubleTapGesture;
    bool m_mobileDebugConsoleToggleRequested = false;
    bool m_previousLeftMouseButtonHeld = false;
    bool m_previousRightMouseButtonHeld = false;
    bool m_previousMiddleMouseButtonHeld = false;
    bool m_suppressLeftMouseButtonUntilReleased = false;
    bool m_suppressRightMouseButtonUntilReleased = false;
    bool m_suppressMiddleMouseButtonUntilReleased = false;
};
} // namespace OpenYAMM::Game
