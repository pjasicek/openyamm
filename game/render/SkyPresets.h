#pragma once

#include "engine/AssetFileSystem.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
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

// A planetary ring along the moon's path, so the moon always hangs in it, and small lights orbiting in it
// (orbit_ring in sky.yml). Off (opacity 0, no lights) unless a preset asks for it; no shipped MM preset does.
struct SkyOrbitRing
{
    // Brightness at full star visibility; the ring fades with the stars, to a pale ghost by day.
    float opacity = 0.0f;
    float widthDegrees = 4.0f;
    SkyColor color = {0.85f, 0.82f, 0.9f};
    // Extra brightness of the debris clumps near the moon (the fragments trailing from it).
    float fragments = 1.0f;
    // Lights orbiting in the ring (gun platforms, stations): count, angular radius, game minutes per orbit.
    int lightCount = 0;
    float lightSizeDegrees = 0.12f;
    std::array<float, 2> lightOrbitMinutes = {60.0f, 180.0f};
    SkyColor lightColor = {1.0f, 0.86f, 0.62f};
    float lightBrightness = 2.0f;
};

constexpr int MaxSkyOrbitLights = 8;

struct SkyStarField
{
    std::string texture;
    float density = 0.6f;
    float brightness = 1.0f;
    float poleElevationDegrees = 55.0f;
};

// Space past the world's edge (a map's terrain.void, U-12): what the sky shows below the horizon over the void.
// Used only on maps with void cells; a preset or theme `void` block sets it, a theme's overriding the preset's.
struct SkyVoidLook
{
    // Linear RGB of empty space.
    SkyColor color = {0.004f, 0.006f, 0.016f};
    // Star brightness below the horizon, by day and night.
    float stars = 0.9f;
    // Depth below the horizon over which the horizon's haze turns into space (the air's limb).
    float limbDegrees = 3.0f;
};

struct SkyPreset
{
    std::string name;
    std::array<SkyTrack, SkyValueCount> tracks;
    float sunDiscDegrees = 1.6f;
    float moonDiscDegrees = 2.2f;
    // The moon disc's texture (engine/rendering/sky/<name>.oytex): a world's preset may draw its own moon.
    std::string moonTexture = "moon";
    // Added to the calendar's moon phase (0 = new, 0.5 = full): where in its cycle a world's moon starts.
    float moonPhaseOffset = 0.0f;
    SkyBelowHorizon belowHorizon = SkyBelowHorizon::Fog;
    // Sky share of world fog colour when the map authors a fog colour or tint.
    float fogTintSkyMix = 0.25f;
    SkyHorizonRing horizonRing;
    SkyStarField stars;
    SkyOrbitRing orbitRing;
    std::optional<SkyVoidLook> voidLook;
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

// A glow along part of the horizon, fixed in world direction (D-36: the bright face's rim seen from the Darkside's
// edge): it climbs heightDegrees above the horizon and shows belowDegrees under it where no land covers it (the
// void), behind the clouds, in its own colour. Its strength blends from day to night by the preset's star weight.
struct SkyRimGlow
{
    // Compass bearing of its middle: 0 north (+Y), 90 east (+X).
    float directionDegrees = 90.0f;
    // Its full width along the horizon.
    float widthDegrees = 75.0f;
    float heightDegrees = 10.0f;
    float belowDegrees = 2.0f;
    SkyColor color = {1.0f, 0.92f, 0.75f};
    float dayStrength = 0.0f;
    float nightStrength = 0.0f;
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
    std::optional<SkyRimGlow> rimGlow;
    std::optional<SkyVoidLook> voidLook;
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
    // Every legacy sky name the library knows (lower case): all the names the data can select.
    std::vector<std::string> skyNames() const;
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

// The sky library with the worlds' own skies (worldTexts: world id, its rendering/sky/sky.yml): a world file has the
// library's version and may hold aliases, presets, themes and maps, each a name the library and the other worlds do
// not define (a world adds skies; it changes none). Its presets may inherit the engine's. composed is the library's
// YAML text.
bool composeSkyLibraryYaml(
    const std::string &engineText,
    const std::vector<std::pair<std::string, std::string>> &worldTexts,
    std::string &composed,
    std::string &errorMessage);

// engine/rendering/sky/sky.yml composed with every mounted world's worlds/<id>/rendering/sky/sky.yml; nothing when it
// cannot be read or composed (errorMessage says why).
std::optional<std::string> readSkyLibraryYaml(const Engine::AssetFileSystem &assets, std::string &errorMessage);
}
