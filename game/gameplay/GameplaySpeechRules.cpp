#include "game/gameplay/GameplaySpeechRules.h"

namespace OpenYAMM::Game
{
namespace
{
bool bypassSpeechCooldown(SpeechId speechId)
{
    switch (speechId)
    {
        case SpeechId::DamageMinor:
        case SpeechId::DamageMajor:
            return true;
        default:
            return false;
    }
}
}

bool canPlaySpeechReactionForPresentationState(
    const GameplayPortraitPresentationState &presentationState,
    size_t memberIndex,
    SpeechId speechId,
    uint32_t nowTicks)
{
    if (memberIndex >= presentationState.memberSpeechCooldownUntilTicks.size())
    {
        return true;
    }

    if (bypassSpeechCooldown(speechId))
    {
        return true;
    }

    if (nowTicks < presentationState.memberSpeechCooldownUntilTicks[memberIndex])
    {
        return false;
    }

    switch (speechId)
    {
        case SpeechId::KillWeakEnemy:
        case SpeechId::KillStrongEnemy:
            return true;

        case SpeechId::AttackHit:
        case SpeechId::AttackMiss:
        case SpeechId::Shoot:
        case SpeechId::CastSpell:
        case SpeechId::DamagedParty:
            return nowTicks >= presentationState.memberCombatSpeechCooldownUntilTicks[memberIndex];

        default:
            return true;
    }
}
}
