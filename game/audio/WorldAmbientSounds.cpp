#include "game/audio/WorldAmbientSounds.h"

#include "game/audio/GameAudioSystem.h"
#include "game/events/EventRuntime.h"

#include <algorithm>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
bool worldAmbientSoundDaytime(float gameMinutes, const WorldAmbientSoundRules &rules)
{
    const float hour = std::fmod(std::max(gameMinutes, 0.0f) / 60.0f, 24.0f);
    return hour >= rules.dayStartHour && hour < rules.dayEndHour;
}

bool worldAmbientSoundAudible(
    const WorldAmbientSound &source,
    const std::array<float, 3> &listener,
    float gameMinutes,
    bool playing,
    std::optional<bool> switchedOn,
    const WorldAmbientSoundRules &rules)
{
    if (!switchedOn.value_or(source.startOn) || source.outerRadius <= 0.0f)
    {
        return false;
    }

    const bool day = worldAmbientSoundDaytime(gameMinutes, rules);

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

std::optional<bool> worldAmbientSoundSwitch(
    const WorldAmbientSound &source,
    const std::unordered_map<std::string, int32_t> *pNamedMapVars)
{
    if (pNamedMapVars == nullptr)
    {
        return std::nullopt;
    }

    const auto iterator = pNamedMapVars->find("AmbientSound" + std::to_string(source.key));

    if (iterator == pNamedMapVars->end() || (iterator->second != 1 && iterator->second != 2))
    {
        return std::nullopt;
    }

    return iterator->second == 1;
}

std::optional<bool> worldAmbientSoundEventSwitch(const WorldAmbientSound &source, const EventRuntimeState *pEvents)
{
    if (pEvents == nullptr)
    {
        return std::nullopt;
    }

    if (const std::optional<bool> switched = worldAmbientSoundSwitch(source, &pEvents->namedMapVars))
    {
        return switched;
    }

    if (source.spriteCog == 0)
    {
        return std::nullopt;
    }

    const auto iterator = pEvents->spriteOverrides.find(source.spriteCog);

    if (iterator == pEvents->spriteOverrides.end())
    {
        return std::nullopt;
    }

    return !iterator->second.hidden;
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
    float deltaSeconds,
    const EventRuntimeState *pEvents,
    const WorldAmbientSoundRules &rules)
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

        const bool audible = worldAmbientSoundAudible(
            source, listener, gameMinutes, voice.audible, worldAmbientSoundEventSwitch(source, pEvents), rules);

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
            source.outerRadius,
            rules.pan);
        voice.playedOnce = true;
        voice.failed = voice.instanceId == 0;
    }
}
}
