#include "game/gameplay/GameplayFxService.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/fx/WorldFxSystem.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include "engine/AssetFileSystem.h"
#include "engine/models/ModelAnimation.h"

#include <algorithm>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float NormalEpsilonSquared = 1.0e-8f;

uint32_t withAlpha(uint32_t colorAbgr, uint8_t alpha)
{
    return (colorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
}

std::optional<std::array<float, 4>> rotationFromPositiveZ(const std::array<float, 3> &direction)
{
    const float lengthSquared = direction[0] * direction[0]
        + direction[1] * direction[1]
        + direction[2] * direction[2];
    if (!std::isfinite(lengthSquared) || lengthSquared <= NormalEpsilonSquared)
    {
        return std::nullopt;
    }

    const float inverseLength = 1.0f / std::sqrt(lengthSquared);
    const std::array<float, 3> normal = {
        direction[0] * inverseLength,
        direction[1] * inverseLength,
        direction[2] * inverseLength,
    };
    if (normal[2] < -0.9999f)
    {
        return std::array<float, 4>{1.0f, 0.0f, 0.0f, 0.0f};
    }

    std::array<float, 4> rotation = {-normal[1], normal[0], 0.0f, 1.0f + normal[2]};
    const float quaternionLength = std::sqrt(
        rotation[0] * rotation[0]
        + rotation[1] * rotation[1]
        + rotation[2] * rotation[2]
        + rotation[3] * rotation[3]);
    for (float &component : rotation)
    {
        component /= quaternionLength;
    }
    return rotation;
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
    m_pendingWorldEffects.clear();
    m_nextWorldEffectSeed = 1;
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
    bool centerVertically,
    size_t targetActorIndex)
{
    return m_session.gameplayProjectileService().spawnProjectileImpactVisual(
        projectile,
        definition,
        x,
        y,
        z,
        centerVertically,
        targetActorIndex);
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
        case PortraitFxEventKind::StatBaseIncrease:
            runtime.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::AwardGain:
            runtime.audioSystem()->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
            break;

        case PortraitFxEventKind::StatDecrease:
        case PortraitFxEventKind::Disease:
        case PortraitFxEventKind::MonsterSpecial:
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

void GameplayFxService::queueMeleeHitBloodEffect(
    const std::array<float, 3> &contactPosition,
    const std::array<float, 3> &outwardNormal)
{
    const std::optional<std::array<float, 4>> rotation = rotationFromPositiveZ(outwardNormal);
    if (!rotation
        || !std::isfinite(contactPosition[0])
        || !std::isfinite(contactPosition[1])
        || !std::isfinite(contactPosition[2]))
    {
        return;
    }

    m_pendingWorldEffects.push_back({
        .id = "mm9:melee_blood",
        .position = contactPosition,
        .rotation = *rotation,
        .scale = 1.0f,
        .seed = m_nextWorldEffectSeed++,
    });
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

void GameplayFxService::consumePendingWorldFxRequests(
    EventRuntimeState *pEventRuntimeState,
    WorldFxSystem &worldFxSystem,
    Engine::AssetFileSystem &assetFileSystem)
{
    for (const PendingWorldEffect &request : m_pendingWorldEffects)
    {
        EffectSpawnParams params;
        params.position = request.position;
        params.rotation = request.rotation;
        params.scale = request.scale;
        params.seed = request.seed;
        const EffectHandle handle = worldFxSystem.namedEffects().spawn(request.id, params);
        if (!worldFxSystem.namedEffects().contains(handle))
        {
            std::cerr << "Gameplay world effect spawn failed: " << request.id << '\n';
        }
    }
    m_pendingWorldEffects.clear();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    for (const EventRuntimeState::WorldEffectRequest &request : pEventRuntimeState->worldEffectRequests)
    {
        const bool validTransform =
            std::isfinite(request.position[0])
            && std::isfinite(request.position[1])
            && std::isfinite(request.position[2])
            && std::isfinite(request.scale)
            && request.scale > 0.0f
            && std::isfinite(request.yawRadians);
        if (request.id.empty() || !validTransform)
        {
            std::cerr << "Ignored invalid scripted world effect request\n";
            continue;
        }

        EffectSpawnParams params;
        params.position = request.position;
        params.rotation = {
            0.0f,
            0.0f,
            std::sin(request.yawRadians * 0.5f),
            std::cos(request.yawRadians * 0.5f),
        };
        params.scale = request.scale;
        const EffectHandle handle = worldFxSystem.namedEffects().spawn(request.id, params);
        if (!worldFxSystem.namedEffects().contains(handle))
        {
            std::cerr << "Scripted world effect spawn failed: " << request.id << '\n';
        }
    }
    pEventRuntimeState->worldEffectRequests.clear();

    for (const EventRuntimeState::WorldModelRequest &request : pEventRuntimeState->worldModelRequests)
    {
        const bool validTransform =
            std::isfinite(request.position[0])
            && std::isfinite(request.position[1])
            && std::isfinite(request.position[2])
            && std::isfinite(request.scale)
            && request.scale > 0.0f
            && std::isfinite(request.yawRadians);
        if (request.assetPath.empty() || !validTransform)
        {
            std::cerr << "Ignored invalid scripted world model request\n";
            continue;
        }

        const Engine::ModelLoadResult loaded =
            worldFxSystem.modelAssets().load(assetFileSystem, request.assetPath);
        if (!loaded)
        {
            std::cerr << "Scripted world model load failed: " << loaded.error << '\n';
            continue;
        }

        const Engine::ModelTransform transform = Engine::gltfModelPlacement(
            request.position,
            request.yawRadians,
            request.scale);
        const Engine::ModelInstanceHandle handle = worldFxSystem.models().create(loaded.asset, transform);
        if (!worldFxSystem.models().contains(handle))
        {
            std::cerr << "Scripted world model spawn failed: " << request.assetPath << '\n';
            continue;
        }
        if (!request.clipName.empty()
            && !worldFxSystem.models().play(handle, request.clipName, Engine::ModelPlaybackMode::Loop))
        {
            worldFxSystem.models().destroy(handle);
            std::cerr << "Scripted world model clip was not found: " << request.clipName << '\n';
        }
    }
    pEventRuntimeState->worldModelRequests.clear();
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
            break;

        case PortraitFxEventKind::AwardGain:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::AwardGot, false);
            break;

        case PortraitFxEventKind::QuestComplete:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::QuestGot, false);
            break;

        case PortraitFxEventKind::StatIncrease:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::StatBonusIncreased, false);
            break;

        case PortraitFxEventKind::StatBaseIncrease:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::StatBaseIncreased, false);
            break;

        case PortraitFxEventKind::StatDecrease:
            break;

        case PortraitFxEventKind::Disease:
            runtime.playSpeechReaction(request.memberIndices.front(), SpeechId::Poisoned, false);
            break;

        case PortraitFxEventKind::MonsterSpecial:
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
