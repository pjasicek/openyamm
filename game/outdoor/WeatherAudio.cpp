#include "game/outdoor/WeatherAudio.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// A loop silent this long is stopped rather than kept playing at zero volume.
constexpr float LoopStopSeconds = 1.0f;
constexpr float CalmWindSpeed = 180.0f;
constexpr float StrongWindSpeed = 700.0f;

float smoothStep(float edge0, float edge1, float value)
{
    const float t = std::clamp((value - edge0) / (edge1 - edge0), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}
}

float WeatherAudio::nextRandom()
{
    uint64_t value = (m_randomState += 0x9e3779b97f4a7c15ull);
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ull;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebull;
    value ^= value >> 31;
    return static_cast<float>(value >> 40) / static_cast<float>(1ull << 24);
}

void WeatherAudio::updateLoop(GameAudioSystem &audio, Loop &loop, const WeatherSound &sound, float volume,
    float deltaSeconds)
{
    const bool playing = loop.instanceId != 0 && audio.isSoundInstancePlaying(loop.instanceId);
    volume *= sound.volume;

    if (volume <= 0.001f || sound.files.empty())
    {
        loop.silentSeconds += deltaSeconds;

        if (playing && loop.silentSeconds >= LoopStopSeconds)
        {
            audio.stopSoundInstance(loop.instanceId);
            loop.instanceId = 0;
        }
        else if (playing)
        {
            audio.setSoundInstanceVolume(loop.instanceId, GameAudioSystem::PlaybackGroup::World, 0.0f);
        }

        return;
    }

    loop.silentSeconds = 0.0f;

    if (!playing)
    {
        loop.instanceId = audio.playAssetInstance(sound.files.front(), GameAudioSystem::PlaybackGroup::World,
            std::nullopt, true, volume);
        return;
    }

    audio.setSoundInstanceVolume(loop.instanceId, GameAudioSystem::PlaybackGroup::World, volume);
}

void WeatherAudio::update(GameAudioSystem &audio, const WeatherSounds &sounds, const WeatherPresentation &weather,
    const std::vector<LightningStrike> &strikes, bool audible, float deltaSeconds)
{
    const float dt = std::max(deltaSeconds, 0.0f);
    const float rain = audible ? weather.rainLevel() : 0.0f;
    // Light rain patters; heavier rain brings in the dense roar.
    const float heavyShare = smoothStep(0.3f, 0.85f, rain);
    const float lightVolume = std::sqrt(rain) * 0.9f * (1.0f - 0.6f * heavyShare);
    const float heavyVolume = heavyShare * (0.6f + 0.4f * rain);
    const float windSpeed = std::sqrt(weather.windX() * weather.windX() + weather.windY() * weather.windY());
    const float windVolume = audible ? 0.7f * smoothStep(CalmWindSpeed, StrongWindSpeed, windSpeed) : 0.0f;
    updateLoop(audio, m_rainLight, sounds.rainLight, lightVolume, dt);
    updateLoop(audio, m_rainHeavy, sounds.rainHeavy, heavyVolume, dt);
    updateLoop(audio, m_wind, sounds.wind, windVolume, dt);

    for (const LightningStrike &strike : strikes)
    {
        m_pendingThunder.push_back({strike, strike.thunderDelaySeconds});
    }

    for (PendingThunder &thunder : m_pendingThunder)
    {
        thunder.remainingSeconds -= dt;

        if (thunder.remainingSeconds > 0.0f || !audible)
        {
            continue;
        }

        const WeatherSound &sound = thunder.strike.distance == LightningDistance::Near ? sounds.thunderNear
            : thunder.strike.distance == LightningDistance::Middle ? sounds.thunderMiddle : sounds.thunderFar;

        if (!sound.files.empty())
        {
            const size_t variant = std::min(static_cast<size_t>(nextRandom() * static_cast<float>(sound.files.size())),
                sound.files.size() - 1);
            const float volume = sound.volume * thunder.strike.loudness * (0.75f + 0.25f * nextRandom());
            const float pitch = 0.9f + 0.2f * nextRandom();
            audio.playAssetInstance(sound.files[variant], GameAudioSystem::PlaybackGroup::World, std::nullopt, false,
                volume, pitch);
        }
    }

    // Thunder that was due while inaudible is dropped rather than played late.
    std::erase_if(m_pendingThunder, [](const PendingThunder &thunder) { return thunder.remainingSeconds <= 0.0f; });
}

void WeatherAudio::stop(GameAudioSystem &audio)
{
    for (Loop *pLoop : {&m_rainLight, &m_rainHeavy, &m_wind})
    {
        if (pLoop->instanceId != 0)
        {
            audio.stopSoundInstance(pLoop->instanceId);
        }
    }

    forget();
}

void WeatherAudio::forget()
{
    m_rainLight = {};
    m_rainHeavy = {};
    m_wind = {};
    m_pendingThunder.clear();
}
}
