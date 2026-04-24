#pragma once

#include "game/party/SpeechIds.h"
#include "game/ui/GameplayUiRuntime.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
bool canPlaySpeechReactionForPresentationState(
    const GameplayPortraitPresentationState &presentationState,
    size_t memberIndex,
    SpeechId speechId,
    uint32_t nowTicks);
}
