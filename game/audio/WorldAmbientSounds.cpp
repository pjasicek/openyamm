#include "game/audio/WorldAmbientSounds.h"

#include "game/audio/GameAudioSystem.h"

#include <algorithm>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
bool worldAmbientSoundAudible(
    const WorldAmbientSound &source,
    const std::array<float, 3> &listener,
    float gameMinutes,
    bool playing)
{
    if (!source.startOn || source.outerRadius <= 0.0f)
    {
        return false;
    }

    const float hour = std::fmod(std::max(gameMinutes, 0.0f) / 60.0f, 24.0f);
    const bool day = hour >= 6.0f && hour < 20.0f;

    if ((source.dayOnly && !day) || (source.nightOnly && day))
    {
        return false;
    }

    const float dx = listener[0] - source.position[0];
    const float dy = listener[1] - source.position[1];
    const float dz = listener[2] - source.position[2];
    const float reach = source.outerRadius * (playing ? AmbientSoundStopMargin : 1.0f);
    return dx * dx + dy * dy + dz * dz <= reach * reach;
}

void WorldAmbientSoundRuntime::stopAll(GameAudioSystem &audio)
{
    for (Voice &voice : m_voices)
    {
        if (voice.instanceId != 0)
        {
            audio.stopSoundInstance(voice.instanceId);
        }
    }

    m_voices.clear();
    m_pSources = nullptr;
    m_sourceCount = 0;
}

void WorldAmbientSoundRuntime::update(
    GameAudioSystem &audio,
    const std::vector<WorldAmbientSound> *pSources,
    const std::array<float, 3> &listener,
    float gameMinutes,
    float deltaSeconds)
{
    const size_t sourceCount = pSources != nullptr ? pSources->size() : 0;

    if (pSources != m_pSources || sourceCount != m_sourceCount)
    {
        stopAll(audio);
        m_pSources = pSources;
        m_sourceCount = sourceCount;
        m_voices.resize(sourceCount);
    }

    for (size_t index = 0; index < sourceCount; ++index)
    {
        const WorldAmbientSound &source = (*pSources)[index];
        Voice &voice = m_voices[index];

        if (voice.instanceId != 0 && !audio.isSoundInstancePlaying(voice.instanceId))
        {
            voice.instanceId = 0;
            std::uniform_real_distribution<float> wait(source.waitMinSeconds,
                std::max(source.waitMinSeconds, source.waitMaxSeconds));
            voice.waitSeconds = wait(m_rng);
        }

        const bool audible = worldAmbientSoundAudible(source, listener, gameMinutes, voice.audible);

        if (!audible)
        {
            if (voice.instanceId != 0)
            {
                audio.stopSoundInstance(voice.instanceId);
            }

            voice = {};
            continue;
        }

        const bool waits = source.loop && source.waitMaxSeconds > 0.0f;

        if (!voice.audible && waits)
        {
            // coming into reach: somewhere into its wait, so a shore's waves do not all start together
            std::uniform_real_distribution<float> wait(0.0f, source.waitMaxSeconds);
            voice.waitSeconds = wait(m_rng);
        }

        voice.audible = true;

        if (voice.instanceId != 0 || voice.failed || (!source.loop && voice.playedOnce))
        {
            continue;
        }

        if (waits && voice.waitSeconds > 0.0f)
        {
            voice.waitSeconds -= deltaSeconds;
            continue;
        }

        const std::optional<std::string> path = audio.soundVirtualPathByName(SoundScope::World, source.sound);

        if (!path)
        {
            voice.failed = true;
            continue;
        }

        voice.instanceId = audio.playAssetInstance(
            *path,
            GameAudioSystem::PlaybackGroup::World,
            GameAudioSystem::WorldPosition{source.position[0], source.position[1], source.position[2]},
            source.loop && !waits,
            source.volume,
            1.0f,
            source.innerRadius,
            source.outerRadius);
        voice.playedOnce = true;
        voice.failed = voice.instanceId == 0;
    }
}
}
