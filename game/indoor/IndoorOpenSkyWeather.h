#pragma once

#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/outdoor/WeatherAudio.h"
#include "game/outdoor/WeatherPresentation.h"
#include "game/render/WeatherRenderer.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class GameAudioSystem;
struct SkyFrameState;
struct SkyInputs;

// The outdoor weather over an indoor map's open sky (scene `sky: {weather}`; MM9's outdoor regions as BLVs,
// devdocs/INDOOR_OPEN_SKY.md "Weather"): the same rolls, fades, rain and snow, lightning and sounds as an outdoor map's
// (WeatherModel, WeatherPresentation, WeatherRenderer, WeatherAudio). Inactive, and free, without the opt-in.
class IndoorOpenSkyWeather
{
public:
    // The map's weather profile (GameDataLoader::applyOpenSkyWeatherToSelectedMap); none leaves it inactive.
    void configure(const std::optional<OutdoorWeatherProfile> &profile);
    bool active() const
    {
        return m_profile.has_value();
    }
    // Once per frame: the weather at the game time, faded in real time; a clock jump (rest, travel) shows it at once.
    // Sounds play while audible (the camera in the open, not under water).
    void update(double gameMinutes, float elapsedSeconds, GameAudioSystem *pAudio, bool audible);
    // The sky follows the shown weather, as an outdoor map's.
    void applyToSky(SkyInputs &inputs) const;
    // Rain and snow round the camera into a transparent view after the world; skipped while not shown.
    void render(uint16_t viewId, const std::array<float, 3> &camera, float yawRadians, const float *pProjection,
        uint16_t viewHeight, const SkyFrameState *pSky, WeatherQuality quality, const WeatherGroundQuery &ground);
    // Its rain-ring strength for the water renderer (0 without rain).
    float rainRings() const;
    void shutdown(GameAudioSystem *pAudio, bool gpuAlive);
    // The debug console's `weather rain|snow <0-1>`, `clear` and `auto` (none: the rolled weather). Not saved.
    void setDebugPrecipitation(std::optional<PrecipitationKind> kind, float intensity);
    // The rolled weather now, before the fades, for `weather status`.
    WeatherSample targetSample() const
    {
        return m_lastTarget;
    }

private:
    std::optional<OutdoorWeatherProfile> m_profile;
    WeatherPresentation m_presentation;
    WeatherRenderer m_renderer;
    WeatherAudio m_audio;
    bool m_rendererInitializeAttempted = false;
    float m_lastElapsedSeconds = -1.0f;
    double m_lastGameMinutes = 0.0;
    float m_frameSeconds = 0.0f;
    int64_t m_wetnessMinute = -1;
    float m_wetness = 0.0f;
    std::optional<PrecipitationKind> m_debugPrecipitation;
    float m_debugIntensity = 0.0f;
    WeatherSample m_lastTarget = {};
};
}
