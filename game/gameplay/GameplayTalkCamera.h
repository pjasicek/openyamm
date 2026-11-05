#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

// The MM9 talk camera (the conversation bar, level_generation/ui/mm9_talk_dialogue_study_20261102 A): while an MM9
// talk with a speaking actor is open, the view turns to the speaker and tilts so their head sits in the upper part of
// the screen, above the bar that stands on the basebar; when the talk closes the tilt eases back. Each world view owns
// one and calls update once a frame with its camera, before it builds the view.
class GameplayTalkCamera
{
public:
    void update(const GameplayScreenRuntime &screen, float eyeX, float eyeY, float eyeZ, float verticalFovDegrees,
        float deltaSeconds, float &yawRadians, float &pitchRadians);

private:
    bool m_active = false;
    bool m_restoring = false;
    float m_restorePitchRadians = 0.0f;
    float m_lastPitchRadians = 0.0f;
};
}
