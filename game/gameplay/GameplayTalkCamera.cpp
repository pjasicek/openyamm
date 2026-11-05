#include "game/gameplay/GameplayTalkCamera.h"

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <numbers>

namespace OpenYAMM::Game
{
namespace
{
// Where the speaker's head lands: this share of the screen's height from its top.
constexpr float HeadFromTop = 0.22f;
// The head: this share of the actor's height above its feet.
constexpr float HeadShare = 0.88f;
// How fast the view turns and tilts (an exponential ease, per second).
constexpr float EaseRate = 6.0f;
constexpr float RestoreRate = 8.0f;
constexpr float Pi = std::numbers::pi_v<float>;

float wrapAngle(float radians)
{
    while (radians > Pi)
    {
        radians -= 2.0f * Pi;
    }

    while (radians < -Pi)
    {
        radians += 2.0f * Pi;
    }

    return radians;
}

// The speaker: the actor the talk was opened on, else (a talk opened by an event, Bjarni's throne) the nearest actor
// with the talk's RUDE id.
bool findSpeaker(const IGameplayWorldRuntime &world, const EventDialogContent &dialog, float eyeX, float eyeY,
    GameplayRuntimeActorState &speaker)
{
    if (dialog.sourceActorIndex)
    {
        return world.actorRuntimeState(*dialog.sourceActorIndex, speaker);
    }

    bool found = false;
    float nearest = 0.0f;
    GameplayRuntimeActorState actor;

    for (size_t index = 0; index < world.mapActorCount(); ++index)
    {
        if (!world.actorRuntimeState(index, actor) || actor.isDead || actor.mm9RudeId <= 0
            || uint32_t(actor.mm9RudeId) != dialog.sourceId)
        {
            continue;
        }

        const float distance = std::hypot(actor.preciseX - eyeX, actor.preciseY - eyeY);

        if (!found || distance < nearest)
        {
            found = true;
            nearest = distance;
            speaker = actor;
        }
    }

    return found;
}
}

void GameplayTalkCamera::update(const GameplayScreenRuntime &screen, float eyeX, float eyeY, float eyeZ,
    float verticalFovDegrees, float deltaSeconds, float &yawRadians, float &pitchRadians)
{
    const EventDialogContent &dialog = screen.activeEventDialog();
    const IGameplayWorldRuntime *pWorld = screen.worldRuntime();
    GameplayRuntimeActorState actor;
    const bool talking = dialog.isActive && dialog.presentation == EventDialogPresentation::Mm9Rude;
    // A speaker that is no actor (a prop, Bjarni on his throne): the view keeps its heading, the head at eye level.
    const bool speakerActor = talking && pWorld != nullptr && findSpeaker(*pWorld, dialog, eyeX, eyeY, actor);
    const float ease = 1.0f - std::exp(-EaseRate * std::max(deltaSeconds, 0.0f));

    if (talking)
    {
        if (!m_active)
        {
            m_active = true;
            m_restoring = false;
            m_restorePitchRadians = pitchRadians;
        }

        const float dx = actor.preciseX - eyeX;
        const float dy = actor.preciseY - eyeY;
        const float distance = std::hypot(dx, dy);
        float headAngle = 0.0f;

        if (speakerActor && distance >= 1.0f)
        {
            const float headZ =
                actor.preciseZ + float(actor.bodyHeight > 0 ? actor.bodyHeight : actor.height) * HeadShare;
            headAngle = std::atan2(headZ - eyeZ, distance);
            yawRadians = wrapAngle(yawRadians + wrapAngle(std::atan2(dy, dx) - yawRadians) * ease);
        }

        const float halfFov = verticalFovDegrees * 0.5f * Pi / 180.0f;
        // The pitch that puts the head HeadFromTop down the screen (its offset from the centre, as the tangent of the
        // half field of view).
        const float targetPitch = headAngle - std::atan((1.0f - 2.0f * HeadFromTop) * std::tan(halfFov));
        pitchRadians += (targetPitch - pitchRadians) * ease;
        m_lastPitchRadians = pitchRadians;
        return;
    }

    if (m_active)
    {
        m_active = false;
        m_restoring = true;
    }

    // Easing back, unless the player has taken the view (mouse look or the pitch keys moved it since).
    if (m_restoring)
    {
        if (std::abs(pitchRadians - m_lastPitchRadians) > 0.0001f)
        {
            m_restoring = false;
            return;
        }

        const float restore = 1.0f - std::exp(-RestoreRate * std::max(deltaSeconds, 0.0f));
        pitchRadians += (m_restorePitchRadians - pitchRadians) * restore;

        if (std::abs(pitchRadians - m_restorePitchRadians) < 0.002f)
        {
            pitchRadians = m_restorePitchRadians;
            m_restoring = false;
        }

        m_lastPitchRadians = pitchRadians;
    }
}
}
