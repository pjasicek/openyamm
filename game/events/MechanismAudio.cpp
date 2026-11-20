#include "game/events/MechanismAudio.h"

#include "game/events/EvtEnums.h"

#include <utility>

namespace OpenYAMM::Game
{
namespace
{
EventRuntimeState::PendingSound mechanismSoundRequest(const MechanismAudioProfile &profile, const std::string &soundName)
{
    EventRuntimeState::PendingSound request = {};
    request.soundScope = SoundScope::World;
    request.soundName = soundName;
    request.x = profile.x;
    request.y = profile.y;
    request.z = profile.z;
    request.positional = profile.positional;
    request.hasExplicitZ = profile.positional;
    return request;
}

void queueMechanismOneShot(
    EventRuntimeState &runtimeState,
    const MechanismAudioProfile &profile,
    const std::string &soundName)
{
    if (!soundName.empty())
    {
        runtimeState.pendingSounds.push_back(mechanismSoundRequest(profile, soundName));
    }
}

void queueMechanismLoop(
    EventRuntimeState &runtimeState,
    uint64_t audioKey,
    const MechanismAudioProfile &profile,
    const std::string &soundName)
{
    if (soundName.empty())
    {
        return;
    }

    EventRuntimeState::PendingSound request = mechanismSoundRequest(profile, soundName);
    request.kind = EventRuntimeState::PendingSound::Kind::PlayLoopingKeyed;
    request.key = audioKey;
    runtimeState.pendingSounds.push_back(std::move(request));
}
}

void queueMechanismMovementAudio(
    EventRuntimeState &runtimeState,
    uint64_t audioKey,
    const MechanismAudioProfile &profile,
    uint16_t previousState,
    bool wasMoving,
    const RuntimeMechanismState &mechanism)
{
    if (!mechanism.isMoving || (wasMoving && previousState == mechanism.state))
    {
        return;
    }

    const bool opening = mechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening);
    const bool closing = mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing);

    if (!opening && !closing)
    {
        return;
    }

    queueMechanismAudioStop(runtimeState, audioKey);

    if (opening)
    {
        const std::string &startSound = !profile.openStartSound.empty() ? profile.openStartSound : profile.openSound;
        queueMechanismOneShot(runtimeState, profile, startSound);
        queueMechanismLoop(runtimeState, audioKey, profile, profile.openBusySound);
    }
    else
    {
        const std::string &startSound = !profile.closeStartSound.empty() ? profile.closeStartSound : profile.closeSound;
        queueMechanismOneShot(runtimeState, profile, startSound);
        queueMechanismLoop(runtimeState, audioKey, profile, profile.closeBusySound);
    }
}

void queueMechanismCompletionAudio(
    EventRuntimeState &runtimeState,
    uint64_t audioKey,
    const MechanismAudioProfile &profile,
    const RuntimeMechanismState &mechanism)
{
    queueMechanismAudioStop(runtimeState, audioKey);

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        queueMechanismOneShot(runtimeState, profile, profile.openStopSound);
    }
    else if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed))
    {
        queueMechanismOneShot(runtimeState, profile, profile.closeStopSound);
    }
}

void queueMechanismAudioStop(EventRuntimeState &runtimeState, uint64_t audioKey)
{
    EventRuntimeState::PendingSound request = {};
    request.kind = EventRuntimeState::PendingSound::Kind::StopKeyed;
    request.key = audioKey;
    runtimeState.pendingSounds.push_back(std::move(request));
}
}
