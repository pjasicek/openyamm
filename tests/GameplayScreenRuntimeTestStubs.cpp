#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
GameplayOverlayInteractionState &GameplayScreenRuntime::interactionState() const
{
    static GameplayOverlayInteractionState interactionState = {};
    return interactionState;
}

Party *GameplayScreenRuntime::party() const
{
    return nullptr;
}

const ItemTable *GameplayScreenRuntime::itemTable() const
{
    return nullptr;
}

const StandardItemEnchantTable *GameplayScreenRuntime::standardItemEnchantTable() const
{
    return nullptr;
}

const SpecialItemEnchantTable *GameplayScreenRuntime::specialItemEnchantTable() const
{
    return nullptr;
}

const SpellTable *GameplayScreenRuntime::spellTable() const
{
    return nullptr;
}

void GameplayScreenRuntime::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    (void)memberIndex;
    (void)speechId;
    (void)triggerFaceAnimation;
}

void GameplayScreenRuntime::queueDelayedSpeechReaction(size_t memberIndex, SpeechId speechId, float delaySeconds)
{
    (void)memberIndex;
    (void)speechId;
    (void)delaySeconds;
}

uint32_t GameplayScreenRuntime::animationTicks() const
{
    return 0;
}

void GameplayScreenRuntime::triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId)
{
    (void)memberIndex;
    (void)animationId;
}

void GameplayScreenRuntime::triggerPortraitEventFxWithoutSpeech(size_t memberIndex, PortraitFxEventKind eventKind)
{
    (void)memberIndex;
    (void)eventKind;
}

void GameplayScreenRuntime::triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId animationId)
{
    (void)animationId;
}

void GameplayScreenRuntime::playHouseSound(uint32_t soundId)
{
    (void)soundId;
}

void GameplayScreenRuntime::playCommonUiSound(SoundId soundId)
{
    (void)soundId;
}

void GameplayScreenRuntime::setStatusBarEvent(
    const std::string &text,
    float durationSeconds,
    GameplayUiController::StatusBarEventPriority priority)
{
    (void)text;
    (void)durationSeconds;
    (void)priority;
}

void GameplayScreenRuntime::updateStatusBarEvent(float deltaSeconds) const
{
    (void)deltaSeconds;
}

const GameSettings &GameplayScreenRuntime::settingsSnapshot() const
{
    static GameSettings settings = {};
    return settings;
}

CombatLog &GameplayScreenRuntime::combatLog()
{
    return m_combatLog;
}

void GameplayScreenRuntime::stopAllAudioPlayback()
{
}
}
