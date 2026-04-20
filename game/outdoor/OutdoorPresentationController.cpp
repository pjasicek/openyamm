#include "game/outdoor/OutdoorPresentationController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t MeteorShowerImpactSoundCooldownMs = 120;
constexpr uint64_t StarburstImpactSoundCooldownMs = 120;
constexpr float WalkingSoundMovementSpeedThreshold = 20.0f;
constexpr float WalkingMotionHoldSeconds = 0.125f;
constexpr uint8_t FirstRoadTileId = 198;
constexpr uint8_t EndRoadTileId = 234;
constexpr uint8_t EndDirtTileId = 90;

std::optional<uint8_t> sampleOutdoorTerrainTileId(const OutdoorMapData &outdoorMapData, float x, float y)
{
    if (outdoorMapData.tileMap.empty())
    {
        return std::nullopt;
    }

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const size_t tileIndex = static_cast<size_t>(tileY * OutdoorMapData::TerrainWidth + tileX);

    if (tileIndex >= outdoorMapData.tileMap.size())
    {
        return std::nullopt;
    }

    return outdoorMapData.tileMap[tileIndex];
}

bool isRoadTerrainTileId(uint8_t tileId)
{
    return tileId >= FirstRoadTileId && tileId < EndRoadTileId;
}

bool isDirtTerrainTileId(uint8_t tileId)
{
    return tileId > 0 && tileId < EndDirtTileId;
}
} // namespace

void OutdoorPresentationController::consumePendingWorldAudioEvents(OutdoorGameView &view)
{
    if (view.m_pGameAudioSystem == nullptr || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const std::vector<OutdoorWorldRuntime::AudioEvent> &events = view.m_pOutdoorWorldRuntime->pendingAudioEvents();

    if (events.empty())
    {
        return;
    }

    for (const OutdoorWorldRuntime::AudioEvent &event : events)
    {
        const uint64_t currentTicks = SDL_GetTicks();

        if (event.reason == "meteor_shower_impact")
        {
            if (currentTicks < view.m_lastMeteorShowerImpactSoundTicks + MeteorShowerImpactSoundCooldownMs)
            {
                continue;
            }

            view.m_lastMeteorShowerImpactSoundTicks = currentTicks;
        }
        else if (event.reason == "starburst_impact")
        {
            if (currentTicks < view.m_lastStarburstImpactSoundTicks + StarburstImpactSoundCooldownMs)
            {
                continue;
            }

            view.m_lastStarburstImpactSoundTicks = currentTicks;
        }

        std::optional<GameAudioSystem::WorldPosition> position = std::nullopt;

        if (event.positional)
        {
            position = GameAudioSystem::WorldPosition{event.x, event.y, event.z};
        }

        view.m_pGameAudioSystem->playSound(event.soundId, GameAudioSystem::PlaybackGroup::World, position);
    }

    view.m_pOutdoorWorldRuntime->clearPendingAudioEvents();
}

void OutdoorPresentationController::consumePendingEventRuntimeAudioRequests(OutdoorGameView &view)
{
    if (view.m_pGameAudioSystem == nullptr || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr || pEventRuntimeState->pendingSounds.empty())
    {
        return;
    }

    const OutdoorMoveState *pMoveState =
        view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->movementState() : nullptr;

    for (const EventRuntimeState::PendingSound &request : pEventRuntimeState->pendingSounds)
    {
        std::optional<GameAudioSystem::WorldPosition> position = std::nullopt;

        if (request.positional)
        {
            position = GameAudioSystem::WorldPosition{
                static_cast<float>(request.x),
                static_cast<float>(request.y),
                pMoveState != nullptr ? pMoveState->footZ + view.m_cameraEyeHeight : 0.0f
            };
        }

        view.m_pGameAudioSystem->playSound(
            request.soundId,
            request.positional ? GameAudioSystem::PlaybackGroup::World : GameAudioSystem::PlaybackGroup::Ui,
            position);
    }

    pEventRuntimeState->pendingSounds.clear();
}

void OutdoorPresentationController::updateFootstepAudio(OutdoorGameView &view, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || view.m_pGameAudioSystem == nullptr || view.m_pOutdoorPartyRuntime == nullptr || !view.m_outdoorMapData)
    {
        return;
    }

    if (resolveGameplayHudScreenState(view.m_gameplayUiController, view.m_activeEventDialog, view.m_pOutdoorWorldRuntime)
        != GameplayHudScreenState::Gameplay)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_walkingMotionHoldSeconds = 0.0f;
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    if (!view.m_walkSoundEnabled)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_walkingMotionHoldSeconds = 0.0f;
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();

    if (!view.m_hasLastFootstepPosition)
    {
        view.m_lastFootstepX = moveState.x;
        view.m_lastFootstepY = moveState.y;
        view.m_hasLastFootstepPosition = true;
        return;
    }

    const float deltaX = moveState.x - view.m_lastFootstepX;
    const float deltaY = moveState.y - view.m_lastFootstepY;
    view.m_lastFootstepX = moveState.x;
    view.m_lastFootstepY = moveState.y;
    const float movedDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
    const float movementSpeed = movedDistance / std::max(deltaSeconds, 0.0001f);

    if (movementSpeed >= WalkingSoundMovementSpeedThreshold)
    {
        view.m_walkingMotionHoldSeconds = WalkingMotionHoldSeconds;
    }
    else
    {
        view.m_walkingMotionHoldSeconds = std::max(0.0f, view.m_walkingMotionHoldSeconds - deltaSeconds);
    }

    if (moveState.airborne || view.m_walkingMotionHoldSeconds <= 0.0f)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const OutdoorPartyMovementState &partyMovementState = view.m_pOutdoorPartyRuntime->partyMovementState();
    const bool running = partyMovementState.running;

    const auto chooseBModelFootstepSound =
        [&view, running, &moveState]() -> SoundId
        {
            if (!view.m_outdoorMapData
                || moveState.supportKind != OutdoorSupportKind::BModelFace
                || moveState.supportBModelIndex >= view.m_outdoorMapData->bmodels.size())
            {
                return running ? SoundId::RunStone : SoundId::WalkStone;
            }

            const OutdoorBModel &bmodel = view.m_outdoorMapData->bmodels[moveState.supportBModelIndex];

            if (moveState.supportFaceIndex >= bmodel.faces.size())
            {
                return running ? SoundId::RunStone : SoundId::WalkStone;
            }

            const std::string textureName = toLowerCopy(bmodel.faces[moveState.supportFaceIndex].textureName);

            if (textureName.find("wood") != std::string::npos || textureName.find("plank") != std::string::npos)
            {
                return running ? SoundId::RunWood : SoundId::WalkWood;
            }

            if (textureName.find("carpet") != std::string::npos || textureName.find("rug") != std::string::npos)
            {
                return running ? SoundId::RunCarpet : SoundId::WalkCarpet;
            }

            if (textureName.find("road") != std::string::npos)
            {
                return running ? SoundId::RunRoad : SoundId::WalkRoad;
            }

            if (textureName.find("dirt") != std::string::npos || textureName.find("earth") != std::string::npos)
            {
                return running ? SoundId::RunDirt : SoundId::WalkDirt;
            }

            return running ? SoundId::RunStone : SoundId::WalkStone;
        };

    const auto chooseTerrainFootstepSound =
        [&view, running, &moveState]() -> SoundId
        {
            if (!view.m_outdoorMapData || moveState.supportKind != OutdoorSupportKind::Terrain)
            {
                return running ? SoundId::RunGrass : SoundId::WalkGrass;
            }

            const std::optional<uint8_t> terrainTileId =
                sampleOutdoorTerrainTileId(*view.m_outdoorMapData, moveState.x, moveState.y);

            if (!terrainTileId.has_value())
            {
                return running ? SoundId::RunGrass : SoundId::WalkGrass;
            }

            if (isRoadTerrainTileId(*terrainTileId))
            {
                return running ? SoundId::RunRoad : SoundId::WalkRoad;
            }

            if (isDirtTerrainTileId(*terrainTileId))
            {
                return running ? SoundId::RunDirt : SoundId::WalkDirt;
            }

            return running ? SoundId::RunGrass : SoundId::WalkGrass;
        };

    const SoundId desiredSoundId = moveState.supportKind == OutdoorSupportKind::BModelFace
        ? chooseBModelFootstepSound()
        : chooseTerrainFootstepSound();

    if (view.m_activeWalkingSoundId == desiredSoundId)
    {
        return;
    }

    view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
    const bool played =
        view.m_pGameAudioSystem->playLoopingSound(
            static_cast<uint32_t>(desiredSoundId),
            GameAudioSystem::PlaybackGroup::Walking);

    view.m_activeWalkingSoundId = played ? std::optional<SoundId>(desiredSoundId) : std::nullopt;
}
} // namespace OpenYAMM::Game
