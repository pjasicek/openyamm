#pragma once

#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/outdoor/WeatherAudio.h"
#include "game/outdoor/WeatherPresentation.h"
#include "game/render/WeatherRenderer.h"
#include "game/render/WeatherRoofMap.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class GameAudioSystem;
struct IndoorMapData;
struct SkyFrameState;
struct SkyInputs;

// The map's roof map for the weather: its drawn surfaces seen from the sky (not its sky faces, portals or invisible
// faces), so rain and snow stop at roofs, bridges and the ground over tunnels.
WeatherRoofMap buildIndoorWeatherRoofMap(const IndoorMapData &mapData);

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
    // The surfaces rain and snow stop at (buildIndoorWeatherRoofMap); without one the weather shows only with the
    // camera in a sector open to the sky (IndoorRenderer).
    void setRoofMap(WeatherRoofMap roofMap);
    bool hasRoofMap() const
    {
        return !m_roofMap.empty() && !m_roofMapUnusable;
    }
    // Whether the camera is under a roof map surface (in a house, under a bridge, in a tunnel).
    bool covers(float x, float y, float z) const;
    // Once per frame: the weather at the game time, faded in real time; a clock jump (rest, travel) shows it at once.
    // Sounds play at the audibility (WeatherAudio: 1 in the open, less under cover, 0 under water), which the
    // sound follows over a fraction of a second, as when walking through a door.
    void update(double gameMinutes, float elapsedSeconds, GameAudioSystem *pAudio, float audibility);
    // The sky follows the shown weather, as an outdoor map's; a fog day hazes it toward its fog colour.
    void applyToSky(SkyInputs &inputs) const;
    // The day's fog (weather.yml fog chances, open_sky_fog distances) at the last update; not foggy on a clear day.
    const WeatherOpenSkyFog &fog() const
    {
        return m_fog;
    }
    // Rain and snow round the camera into a transparent view after the world; skipped while not shown.
    // Under cover the distant rain curtain is left out (it would hang inside the room). pHaze: the scene fog's colour
    // this frame (display space), which the drops and flakes fall through; null without fog.
    void render(uint16_t viewId, const std::array<float, 3> &camera, float yawRadians, const float *pProjection,
        uint16_t viewHeight, const SkyFrameState *pSky, WeatherQuality quality, const WeatherGroundQuery &ground,
        bool covered, const std::array<float, 3> *pHaze);
    // Its rain-ring strength for the water renderer (0 without rain).
    float rainRings() const;
    void shutdown(GameAudioSystem *pAudio, bool gpuAlive);
    // The debug console's `weather rain|snow <0-1>`, `clear` and `auto` (none: the rolled weather). Not saved.
    void setDebugPrecipitation(std::optional<PrecipitationKind> kind, float intensity);
    // The debug console's `weather fog none|small|average|dense` and `fog auto` (none: the rolled fog). Not saved.
    void setDebugFog(std::optional<WeatherFogLevel> level)
    {
        m_debugFog = level;
    }
    // The rolled weather now, before the fades, for `weather status`.
    WeatherSample targetSample() const
    {
        return m_lastTarget;
    }
    // The shown weather, for `weather status`.
    const WeatherPresentation &presentation() const
    {
        return m_presentation;
    }
    float audibility() const
    {
        return m_audibility;
    }
    // The console's `weather strike`: a lightning strike now (thunder follows).
    void forceStrike(LightningDistance distance)
    {
        m_presentation.forceStrike(distance);
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
    std::optional<WeatherFogLevel> m_debugFog;
    WeatherOpenSkyFog m_fog = {};
    WeatherSample m_lastTarget = {};
    WeatherRoofMap m_roofMap;
    bool m_roofMapUploaded = false;
    bool m_roofMapUnusable = false;
    float m_audibility = 0.0f;
};
}
