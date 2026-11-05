#include "game/indoor/IndoorOpenSkyWeather.h"

#include "game/audio/GameAudioSystem.h"
#include "game/render/SkyRenderer.h"
#include "game/render/SkyState.h"

#include <algorithm>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
// As the outdoor view (OutdoorRenderer): rain or snow below this shown strength leaves the sky as it is, and a game
// clock jump over this many minutes shows the new weather at once.
constexpr float ShownPrecipitationThreshold = 0.03f;
constexpr double SnapGameMinutes = 30.0;
}

void IndoorOpenSkyWeather::configure(const std::optional<OutdoorWeatherProfile> &profile)
{
    m_profile = profile;
    m_presentation = {};
    m_lastElapsedSeconds = -1.0f;
    m_frameSeconds = 0.0f;
    m_wetnessMinute = -1;
    m_wetness = 0.0f;
}

void IndoorOpenSkyWeather::update(double gameMinutes, float elapsedSeconds, GameAudioSystem *pAudio, bool audible)
{
    if (!m_profile)
    {
        return;
    }

    const WeatherRules &rules = m_profile->weatherRules;
    const WeatherMapSettings &settings = m_profile->weatherMap;
    WeatherSample target = sampleRolledWeather(rules, settings, gameMinutes);
    // Wetness integrates hours of weather: resampled once per game minute, as the outdoor runtime does.
    const int64_t minute = static_cast<int64_t>(std::floor(gameMinutes));

    if (minute != m_wetnessMinute)
    {
        m_wetness = sampleWetness(rules, settings, static_cast<double>(minute));
        m_wetnessMinute = minute;
    }

    target.wetness = m_wetness;
    if (m_debugPrecipitation)
    {
        // As the outdoor console override: the kind at the given strength, under clouds to match.
        target.precipitation = *m_debugPrecipitation;
        target.intensity = *m_debugPrecipitation == PrecipitationKind::None ? 0.0f : m_debugIntensity;
        target.cloudCover = std::max(target.cloudCover, target.intensity > 0.0f ? 0.6f + 0.4f * target.intensity : 0.0f);
    }
    m_lastTarget = target;
    m_frameSeconds = 0.0f;

    if (m_lastElapsedSeconds < 0.0f || std::abs(gameMinutes - m_lastGameMinutes) > SnapGameMinutes)
    {
        m_presentation.snap();
    }
    else
    {
        m_frameSeconds = std::max(elapsedSeconds - m_lastElapsedSeconds, 0.0f);
    }

    m_lastElapsedSeconds = elapsedSeconds;
    m_lastGameMinutes = gameMinutes;
    m_presentation.update(rules, target, m_frameSeconds);
    const std::vector<LightningStrike> strikes = m_presentation.takeStrikes();

    if (pAudio != nullptr)
    {
        m_audio.update(*pAudio, rules.sounds, m_presentation, strikes, audible, m_frameSeconds);
    }
}

void IndoorOpenSkyWeather::applyToSky(SkyInputs &inputs) const
{
    if (!m_profile)
    {
        return;
    }

    inputs.raining = m_presentation.rainLevel() > ShownPrecipitationThreshold;
    inputs.snowing = !inputs.raining && m_presentation.snowLevel() > ShownPrecipitationThreshold;
    inputs.precipitation = std::max(m_presentation.rainLevel(), m_presentation.snowLevel());
    inputs.lightningFlash = m_presentation.lightningFlash();
}

float IndoorOpenSkyWeather::rainRings() const
{
    if (!m_profile)
    {
        return 0.0f;
    }

    const float rain = m_presentation.rainLevel();
    return std::min(1.0f, rain * 10.0f) * (0.15f + 0.75f * rain);
}

void IndoorOpenSkyWeather::render(uint16_t viewId, const std::array<float, 3> &camera, float yawRadians,
    const float *pProjection, uint16_t viewHeight, const SkyFrameState *pSky, WeatherQuality quality,
    const WeatherGroundQuery &ground)
{
    if (!m_profile || quality == WeatherQuality::Off
        || (m_presentation.rainLevel() <= 0.0f && m_presentation.snowLevel() <= 0.0f
            && m_presentation.ashLevel() <= 0.0f))
    {
        m_renderer.resetCamera();
        return;
    }

    if (!m_renderer.isReady())
    {
        if (m_rendererInitializeAttempted)
        {
            return;
        }

        m_rendererInitializeAttempted = true;

        if (!m_renderer.initialize())
        {
            std::cerr << "Cannot create weather rendering resources.\n";
            return;
        }
    }

    // Lit as the outdoor view lights it: the sky's brightness with part of its hue, dimmed by cloud, lit by lightning.
    std::array<float, 3> light = {0.6f, 0.6f, 0.6f};

    if (pSky != nullptr)
    {
        const std::array<float, 3> tint = skyEnvironmentTint(*pSky);
        const float luminance = 0.2126f * tint[0] + 0.7152f * tint[1] + 0.0722f * tint[2];

        for (size_t channel = 0; channel < 3; ++channel)
        {
            light[channel] = 0.05f + 0.9f * std::min(luminance + (tint[channel] - luminance) * 0.35f, 1.3f);
        }
    }

    const float cloudDimming = 1.0f - 0.25f * m_presentation.cloudCover();

    for (float &channel : light)
    {
        channel = channel * cloudDimming + 0.9f * m_presentation.lightningFlash();
    }

    const WeatherRules &rules = m_profile->weatherRules;
    const WeatherMapSettings &settings = m_profile->weatherMap;
    WeatherDrawFrame frame;
    frame.camera = camera;
    frame.forward = {std::cos(yawRadians), std::sin(yawRadians)};
    frame.groundHeight = ground;
    frame.deltaSeconds = m_frameSeconds;
    frame.rainLevel = m_presentation.rainLevel();
    frame.snowLevel = m_presentation.snowLevel();
    frame.ashLevel = m_presentation.ashLevel();
    frame.snowLook = rules.snowFlakes;
    frame.ashLook = settings.ashLook.value_or(rules.ashFlakes);
    frame.rainColor = settings.rainColor;
    frame.windX = m_presentation.windX();
    frame.windY = m_presentation.windY();
    frame.light = light;
    frame.pixelWorldSize = 2.0f / std::max(std::abs(pProjection[5]) * static_cast<float>(viewHeight), 1.0f);
    frame.quality = quality;
    m_renderer.render(viewId, frame);
}

void IndoorOpenSkyWeather::setDebugPrecipitation(std::optional<PrecipitationKind> kind, float intensity)
{
    m_debugPrecipitation = kind;
    m_debugIntensity = std::clamp(intensity, 0.0f, 1.0f);
}

void IndoorOpenSkyWeather::shutdown(GameAudioSystem *pAudio, bool gpuAlive)
{
    if (pAudio != nullptr)
    {
        m_audio.stop(*pAudio);
    }
    else
    {
        m_audio.forget();
    }

    if (gpuAlive)
    {
        m_renderer.shutdown();
    }

    m_rendererInitializeAttempted = false;
    m_profile.reset();
}
}
