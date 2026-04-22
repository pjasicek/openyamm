#include "game/gameplay/GameplayFxService.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;

uint32_t withAlpha(uint32_t colorAbgr, uint8_t alpha)
{
    return (colorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
}
}

GameplayFxService::GameplayFxService(GameSession &session)
    : m_session(session)
{
}

void GameplayFxService::clear()
{
    m_gameplayScreenOverlayState = {};
    m_activeProjectilePresentationStates.clear();
    m_activeProjectileImpactPresentationStates.clear();
}

void GameplayFxService::syncProjectilePresentation()
{
    m_activeProjectilePresentationStates.clear();
    m_activeProjectileImpactPresentationStates.clear();

    m_session.gameplayProjectileService().collectProjectilePresentationState(
        m_activeProjectilePresentationStates,
        m_activeProjectileImpactPresentationStates);
}

GameplayProjectileService::ProjectileImpactSpawnResult GameplayFxService::spawnProjectileImpactVisual(
    const GameplayProjectileService::ProjectileState &projectile,
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    return m_session.gameplayProjectileService().spawnProjectileImpactVisual(
        projectile,
        definition,
        x,
        y,
        z,
        centerVertically);
}

GameplayProjectileService::ProjectileImpactSpawnResult GameplayFxService::spawnWaterSplashImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z)
{
    return m_session.gameplayProjectileService().spawnWaterSplashImpactVisual(definition, x, y, z);
}

GameplayProjectileService::ProjectileImpactSpawnResult GameplayFxService::spawnImmediateSpellImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    int sourceSpellId,
    const std::string &sourceObjectName,
    const std::string &sourceObjectSpriteName,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool freezeAnimation)
{
    return m_session.gameplayProjectileService().spawnImmediateSpellImpactVisual(
        definition,
        sourceSpellId,
        sourceObjectName,
        sourceObjectSpriteName,
        x,
        y,
        z,
        centerVertically,
        freezeAnimation);
}

void GameplayFxService::triggerPortraitEventFxWithoutSpeech(
    GameplayScreenRuntime &runtime,
    size_t memberIndex,
    PortraitFxEventKind kind) const
{
    GameplayUiRuntime &uiRuntime = m_session.gameplayUiRuntime();
    const PortraitFxEventEntry *pEntry = uiRuntime.findPortraitFxEvent(kind);

    if (pEntry == nullptr)
    {
        return;
    }

    uiRuntime.triggerPortraitFxAnimation(pEntry->animationName, {memberIndex});

    if (pEntry->faceAnimationId.has_value())
    {
        runtime.triggerPortraitFaceAnimation(memberIndex, *pEntry->faceAnimationId);
    }

    if (runtime.audioSystem() == nullptr)
    {
        return;
    }

    switch (kind)
    {
        case PortraitFxEventKind::AutoNote:
        case PortraitFxEventKind::QuestComplete:
        case PortraitFxEventKind::StatIncrease:
            runtime.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::AwardGain:
            runtime.audioSystem()->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::StatDecrease:
        case PortraitFxEventKind::Disease:
        case PortraitFxEventKind::None:
            break;
    }
}

void GameplayFxService::triggerPortraitSpellFx(const PartySpellCastResult &result) const
{
    m_session.gameplayUiRuntime().triggerPortraitSpellFx(result);
}

void GameplayFxService::triggerGameplayScreenOverlay(
    const PartySpellCastResult::ScreenOverlayRequest &request)
{
    m_gameplayScreenOverlayState.colorAbgr = request.colorAbgr;
    m_gameplayScreenOverlayState.durationSeconds = std::max(request.durationSeconds, 0.0f);
    m_gameplayScreenOverlayState.remainingSeconds = m_gameplayScreenOverlayState.durationSeconds;
    m_gameplayScreenOverlayState.peakAlpha = std::clamp(request.peakAlpha, 0.0f, 1.0f);
}

void GameplayFxService::advanceGameplayScreenOverlay(float deltaSeconds)
{
    if (m_gameplayScreenOverlayState.remainingSeconds <= 0.0f)
    {
        return;
    }

    m_gameplayScreenOverlayState.remainingSeconds =
        std::max(0.0f, m_gameplayScreenOverlayState.remainingSeconds - std::max(deltaSeconds, 0.0f));
}

void GameplayFxService::renderGameplayScreenOverlay(
    GameplayScreenRuntime &runtime,
    int width,
    int height) const
{
    if (width <= 0
        || height <= 0
        || m_gameplayScreenOverlayState.remainingSeconds <= 0.0f
        || m_gameplayScreenOverlayState.durationSeconds <= 0.0f)
    {
        return;
    }

    const float elapsedSeconds =
        m_gameplayScreenOverlayState.durationSeconds - m_gameplayScreenOverlayState.remainingSeconds;
    const float normalizedTime =
        std::clamp(elapsedSeconds / m_gameplayScreenOverlayState.durationSeconds, 0.0f, 1.0f);
    const float overlayAlpha =
        std::sin(normalizedTime * Pi) * m_gameplayScreenOverlayState.peakAlpha;

    if (overlayAlpha <= 0.0f)
    {
        return;
    }

    const long alpha =
        std::clamp(std::lround(overlayAlpha * 255.0f), 0l, 255l);
    const std::optional<GameplayScreenRuntime::HudTextureHandle> texture =
        runtime.gameplayUiRuntime().ensureSolidHudTextureLoaded(
            "GameplayScreenOverlay",
            withAlpha(m_gameplayScreenOverlayState.colorAbgr, static_cast<uint8_t>(alpha)));

    if (!texture.has_value())
    {
        return;
    }

    runtime.prepareHudView(width, height);
    runtime.submitHudTexturedQuad(*texture, 0.0f, 0.0f, static_cast<float>(width), static_cast<float>(height));
}

void GameplayFxService::consumePendingEventFxRequests(GameplayScreenRuntime &runtime) const
{
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    for (const EventRuntimeState::PortraitFxRequest &request : pEventRuntimeState->portraitFxRequests)
    {
        consumePendingPortraitEventFxRequest(runtime, request);
    }

    pEventRuntimeState->portraitFxRequests.clear();

    for (const EventRuntimeState::SpellFxRequest &request : pEventRuntimeState->spellFxRequests)
    {
        consumePendingSpellFxRequest(runtime, request);
    }

    pEventRuntimeState->spellFxRequests.clear();
}

const std::vector<GameplayProjectilePresentationState> &GameplayFxService::activeProjectilePresentationStates() const
{
    return m_activeProjectilePresentationStates;
}

const std::vector<GameplayProjectileImpactPresentationState> &
GameplayFxService::activeProjectileImpactPresentationStates() const
{
    return m_activeProjectileImpactPresentationStates;
}

void GameplayFxService::consumePendingPortraitEventFxRequest(
    GameplayScreenRuntime &runtime,
    const EventRuntimeState::PortraitFxRequest &request) const
{
    GameplayUiRuntime &uiRuntime = m_session.gameplayUiRuntime();
    const PortraitFxEventEntry *pEntry = uiRuntime.findPortraitFxEvent(request.kind);

    if (pEntry == nullptr)
    {
        return;
    }

    uiRuntime.triggerPortraitFxAnimation(pEntry->animationName, request.memberIndices);

    if (pEntry->faceAnimationId.has_value())
    {
        for (size_t memberIndex : request.memberIndices)
        {
            runtime.triggerPortraitFaceAnimation(memberIndex, *pEntry->faceAnimationId);
        }
    }

    if (request.memberIndices.empty())
    {
        return;
    }

    switch (request.kind)
    {
        case PortraitFxEventKind::AutoNote:
            if (runtime.audioSystem() != nullptr)
            {
                runtime.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            }
            break;

        case PortraitFxEventKind::AwardGain:
            if (runtime.audioSystem() != nullptr)
            {
                runtime.audioSystem()->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
            }
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::AwardGot, false);
            break;

        case PortraitFxEventKind::QuestComplete:
            if (runtime.audioSystem() != nullptr)
            {
                runtime.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            }
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::QuestGot, false);
            break;

        case PortraitFxEventKind::StatIncrease:
            if (runtime.audioSystem() != nullptr)
            {
                runtime.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            }
            break;

        case PortraitFxEventKind::StatDecrease:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::Indignant, false);
            break;

        case PortraitFxEventKind::Disease:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::Poisoned, false);
            break;

        case PortraitFxEventKind::None:
            break;
    }
}

void GameplayFxService::consumePendingSpellFxRequest(
    GameplayScreenRuntime &runtime,
    const EventRuntimeState::SpellFxRequest &request) const
{
    triggerPortraitSpellFx(PartySpellCastResult{
        .spellId = request.spellId,
        .affectedCharacterIndices = request.memberIndices
    });

    if (runtime.audioSystem() == nullptr || runtime.spellTable() == nullptr)
    {
        return;
    }

    const SpellEntry *pSpellEntry = runtime.spellTable()->findById(request.spellId);

    if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
    {
        runtime.audioSystem()->playSound(pSpellEntry->effectSoundId, GameAudioSystem::PlaybackGroup::Ui);
    }
}
}
