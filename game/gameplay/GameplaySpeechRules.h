#pragma once

#include "game/party/SpeechIds.h"
#include "game/ui/GameplayUiRuntime.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
struct Character;

// Whether a member in their current condition may say this line. Incapacitated members (asleep, paralysed,
// unconscious, dead, stone, eradicated) are silent, except for the lines about losing consciousness (Dying,
// CheatedDeath: queued as health crosses zero, played after) and Awaken unless dead, stone or eradicated.
bool canMemberSpeak(const Character &member, SpeechId speechId);

bool canPlaySpeechReactionForPresentationState(
    const GameplayPortraitPresentationState &presentationState,
    size_t memberIndex,
    SpeechId speechId,
    uint32_t nowTicks);

// Whether the member said this line less than intervalMs ago (the "Repeated voice lines" setting). An interval of 0
// never holds a line back.
bool isRepeatedSpeechReaction(
    const GameplayPortraitPresentationState &presentationState,
    size_t memberIndex,
    SpeechId speechId,
    uint32_t nowTicks,
    uint32_t intervalMs);
}
