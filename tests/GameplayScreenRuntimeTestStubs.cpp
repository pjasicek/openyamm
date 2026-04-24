#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
void GameplayScreenRuntime::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    (void)memberIndex;
    (void)speechId;
    (void)triggerFaceAnimation;
}

void GameplayScreenRuntime::playHouseSound(uint32_t soundId)
{
    (void)soundId;
}

void GameplayScreenRuntime::playCommonUiSound(SoundId soundId)
{
    (void)soundId;
}

void GameplayScreenRuntime::stopAllAudioPlayback()
{
}
}
