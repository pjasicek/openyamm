#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
using SkyColor = std::array<float, 3>;

// Every value a sky preset keys by game time. Colours are linear RGB; scalars use component 0.
enum class SkyValue : uint8_t
{
    Zenith,
    Horizon,
    HorizonExponent,
    SunGlow,
    SunGlowExponent,
    SunGlowStrength,
    Fog,
    SunDisc,
    SunDiscVisibility,
    CloudLit,
    CloudShadow,
    AmbientTint,
    WaterSun,
    WaterSky,
    Stars,
    MoonVisibility,
    AerialHaze,
    Count
};

constexpr size_t SkyValueCount = static_cast<size_t>(SkyValue::Count);

struct SkyValueInfo
{
    const char *pName;
    uint8_t components;
};

const SkyValueInfo &skyValueInfo(SkyValue value);

struct SkyTrackKey
{
    int minute = 0;
    SkyColor value = {};
};

// One value's keys, sorted by minute; evaluation wraps across midnight.
using SkyTrack = std::vector<SkyTrackKey>;

SkyColor evaluateSkyTrack(const SkyTrack &track, float minuteOfDay);

enum class SkyBelowHorizon : uint8_t
{
    Fog,
    Sky,
    Flat,
};

struct SkyCloudLayer
{
    std::string texture;
    float scale = 0.4f;
    float speed = 0.006f;
    float directionDegrees = 30.0f;
    float coverage = 0.4f;
    float softness = 0.2f;
    float opacity = 1.0f;
    float curvature = 0.12f;
    // Colour layers draw a painted texture (the original MM skies) in its own colours, tinted by cloud_lit;
    // density layers shade a coverage map between cloud_shadow and cloud_lit.
    bool color = false;
};

struct SkyHorizonRing
{
    std::string texture;
    float opacity = 0.0f;
    float height = 0.08f;
};

struct SkyStarField
{
    std::string texture;
    float density = 0.6f;
    float brightness = 1.0f;
    float poleElevationDegrees = 55.0f;
};

struct SkyPreset
{
    std::string name;
    std::array<SkyTrack, SkyValueCount> tracks;
    float sunDiscDegrees = 1.6f;
    float moonDiscDegrees = 2.2f;
    SkyBelowHorizon belowHorizon = SkyBelowHorizon::Fog;
    // Sky share of world fog colour when the map authors a fog colour or tint.
    float fogTintSkyMix = 0.25f;
    SkyHorizonRing horizonRing;
    SkyStarField stars;
    std::vector<SkyCloudLayer> clouds;
    // A storm sky keeps its own look in rain instead of switching to the generic rain preset.
    bool storm = false;
    bool drawSky = true;
};

struct SkySpecialPresets
{
    std::string underwater;
    std::string redFog;
    std::string alwaysLight;
    std::string alwaysDark;
    std::string rain;
    std::string snow;
};

// A map's look layered over whichever preset the weather selects, keyed by map file name in `maps`.
struct SkyTheme
{
    std::string name;
    // Replaces the weather and sky-name selection; underwater, debug and special-flag presets still win.
    std::string preset;
    // Multiplies zenith, horizon, fog and water sky colours.
    SkyColor skyTint = {1.0f, 1.0f, 1.0f};
    // Multiplies sun glow, sun disc and water glint colours.
    SkyColor sunTint = {1.0f, 1.0f, 1.0f};
    // Multiplies cloud lit and shadow colours (and the painted original skies).
    SkyColor cloudTint = {1.0f, 1.0f, 1.0f};
    // 0 = grey, 1 = unchanged; applies to sky, fog, sun glow and cloud colours.
    float saturation = 1.0f;
    // Minimum haze toward the themed fog colour (0-1), as with fog weather.
    float haze = 0.0f;
    float starScale = 1.0f;
};

class SkyPresetLibrary
{
public:
    // Parses and validates the whole library; on failure returns false with a message and leaves it empty.
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);

    const SkyPreset *find(const std::string &name) const;
    const SkyPreset *fallback() const;
    // Legacy sky texture name (any case) to preset name, or empty when unknown.
    std::string presetForSkyName(const std::string &skyTextureName) const;
    // Merged MMerge weather ladder position (clear to storm) to preset name.
    std::string presetForWeatherState(int state, int stateCount) const;
    const SkySpecialPresets &specials() const;
    // Theme for a map file name (any case, such as "out04.odm"), or null when the map has none.
    const SkyTheme *themeForMap(const std::string &mapFileName) const;
    const SkyTheme *findTheme(const std::string &name) const;
    float transitionSeconds() const;
    std::vector<std::string> textureNames() const;
    bool empty() const;

private:
    std::unordered_map<std::string, SkyPreset> m_presets;
    std::unordered_map<std::string, std::string> m_aliases;
    std::unordered_map<std::string, SkyTheme> m_themes;
    std::unordered_map<std::string, std::string> m_mapThemes;
    std::vector<std::string> m_weatherLadder;
    SkySpecialPresets m_specials;
    std::string m_fallback;
    float m_transitionSeconds = 45.0f;
};
}
