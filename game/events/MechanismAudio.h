#pragma once

#include "game/events/EventRuntime.h"
#include "game/events/MechanismAudioProfile.h"

#include <cstdint>

namespace OpenYAMM::Game
{
// A mechanism's own sounds (MechanismAudioProfile), shared by the outdoor model mechanisms and the indoor doors: a
// one-shot when it starts to open or close (openStart, else open; closeStart, else close) with its busy loop under the
// caller's key, and a one-shot when it comes to rest open or shut.

// When the mechanism starts moving or turns round (nothing while it keeps moving the same way).
void queueMechanismMovementAudio(
    EventRuntimeState &runtimeState,
    uint64_t audioKey,
    const MechanismAudioProfile &profile,
    uint16_t previousState,
    bool wasMoving,
    const RuntimeMechanismState &mechanism);
// When the mechanism has come to rest (its state Open or Closed).
void queueMechanismCompletionAudio(
    EventRuntimeState &runtimeState,
    uint64_t audioKey,
    const MechanismAudioProfile &profile,
    const RuntimeMechanismState &mechanism);
void queueMechanismAudioStop(EventRuntimeState &runtimeState, uint64_t audioKey);
}
