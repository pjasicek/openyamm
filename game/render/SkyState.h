#pragma once

#include "game/render/SkyPresets.h"

#include <array>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// What the sky needs from the world each frame, independent of the outdoor runtime type.
struct SkyInputs
{
    float gameMinutes = 9.0f * 60.0f;
    std::string weatherSkyName;
    int mergedWeatherState = -1;
    int mergedWeatherStateCount = 0;
    bool underwater = false;
    bool redFog = false;
    bool alwaysLight = false;
    bool alwaysDark = false;
    bool foggy = false;
    float fogStrongDistance = 0.0f;
    bool raining = false;
    bool snowing = false;
    // Shown rain or snow strength (0-1) and this frame's lightning brightness, from the outdoor weather.
    float precipitation = 0.0f;
    float lightningFlash = 0.0f;
    // Map-authored fog colour or tint in display space (0-1), which keeps priority over preset fog colours.
    std::optional<SkyColor> authoredFogDisplay;
    // The original renderer's fog colour for untinted fog weather (neutral grey by daylight), display space.
    std::optional<SkyColor> weatherFogDisplay;
    // Debug `sky preset` override; empty selects automatically.
    std::string forcedPreset;
    // Map file name ("out04.odm") for the map's sky theme.
    std::string mapFileName;
    // Debug `sky theme` override: a theme name, or empty for no theme; unset selects by map.
    std::optional<std::string> forcedTheme;
};

struct SkyCloudLayerState
{
    std::string texture;
    float scale = 0.4f;
    float coverage = 0.4f;
    float softness = 0.2f;
    float opacity = 0.0f;
    float curvature = 0.12f;
    std::array<float, 2> offset = {};
    bool color = false;
};

constexpr size_t MaxSkyCloudLayers = 4;

struct SkyFrameState
{
    std::string presetName;
    std::array<SkyColor, SkyValueCount> values = {};
    // 0 = clear air, 1 = the sky is fully replaced by the fog colour.
    float fogAmount = 0.0f;
    // World fog colour = mix(fogFlatDisplay, sky colour in the view direction, skyMix).
    float skyMix = 1.0f;
    SkyColor fogFlatDisplay = {};
    std::array<float, 3> sunDirection = {0.0f, 0.0f, 1.0f};
    float sunDiscDegrees = 1.6f;
    std::array<float, 3> moonDirection = {0.0f, 0.0f, -1.0f};
    float moonDiscDegrees = 2.2f;
    // 0 = new moon, 0.5 = full moon.
    float moonPhase = 0.5f;
    float starRotationRadians = 0.0f;
    SkyStarField stars;
    SkyHorizonRing horizonRing;
    std::vector<SkyCloudLayerState> clouds;
    float lightningFlash = 0.0f;
    SkyBelowHorizon belowHorizon = SkyBelowHorizon::Fog;
    bool drawSky = true;
    // Active map theme, empty when none.
    std::string themeName;

    const SkyColor &value(SkyValue id) const
    {
        return values[static_cast<size_t>(id)];
    }

    float scalar(SkyValue id) const
    {
        return values[static_cast<size_t>(id)][0];
    }
};

// Sun direction (x east-west, z up) for the shared outdoor sun arc: rises at +X at 05:00, sets at -X at 21:00.
// Matches OutdoorWorldRuntime while the sun is up and continues below the horizon at night.
std::array<float, 3> skySunDirection(float gameMinutes);
std::array<float, 3> skyMoonDirection(float gameMinutes);
float skyMoonPhase(float gameMinutes);

// Whether the preset draws an original painted sky (a colour cloud layer).
bool isPaintedSkyPreset(const SkyPreset &preset);
std::string selectSkyPreset(const SkyPresetLibrary &library, const SkyInputs &inputs);
const SkyTheme *selectSkyTheme(const SkyPresetLibrary &library, const SkyInputs &inputs);

class SkyStateModel
{
public:
    void setLibrary(const SkyPresetLibrary *pLibrary);
    // The next update snaps to its target instead of cross-fading (map load, teleport, save load).
    void snap();
    const SkyFrameState &update(const SkyInputs &inputs, float realDeltaSeconds);
    const SkyFrameState &frame() const;

private:
    void buildCloudLayers(const SkyPreset &from, const SkyPreset &to, float blend, float realDeltaSeconds);

    const SkyPresetLibrary *m_pLibrary = nullptr;
    SkyFrameState m_frame;
    std::string m_fromPreset;
    std::string m_toPreset;
    std::string m_lastForcedPreset;
    float m_blend = 1.0f;
    bool m_snapPending = true;
    float m_lastGameMinutes = 0.0f;
    std::unordered_map<std::string, std::array<float, 2>> m_cloudOffsets;
};
}
