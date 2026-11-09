#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class PrecipitationKind : uint8_t
{
    None = 0,
    Rain = 1,
    Snow = 2,
    // Falling volcanic ash: flakes like snow, but it never settles, wets nothing and is not seasonal. It falls only
    // on maps whose weather.yml entry gives an ash chance.
    Ash = 3,
};

struct WeatherIntensityLevel
{
    std::string name;
    float value = 0.5f;
    float weight = 1.0f;
};

// Length and ramps of one rain or snow spell, in game minutes.
struct WeatherSpellShape
{
    float minMinutes = 120.0f;
    float maxMinutes = 540.0f;
    std::array<float, 2> rampUpMinutes = {20.0f, 60.0f};
    std::array<float, 2> rampDownMinutes = {30.0f, 90.0f};
};

struct WeatherMapChances
{
    std::optional<float> rainPercent;
    std::optional<float> snowPercent;
    std::optional<float> ashPercent;
    // The flake look its ash falls with (a flakes key, e.g. ember); unset: flakes.ash.
    std::optional<std::string> ashLook;
    // The daily chance of dry lightning: strikes without rain all that day.
    std::optional<float> dryLightningPercent;
    // Its rain's colour before the light (acid rain); unset: DefaultRainColor.
    std::optional<std::array<float, 3>> rainColor;
    // Weather that never stops (weather.yml `always: rain|snow` at `peak`): MM9's Rain and Snow brushes, on all the
    // time (Sturmford's rain, Frosgard's snow). Only a kind the map can have; it replaces the daily rolls.
    PrecipitationKind always = PrecipitationKind::None;
    float alwaysPeak = 0.5f;
    // Daily chances of small, average and dense fog (weather.yml `fog: [small, average, dense]`, percent). Only the
    // open sky of an indoor map rolls them (IndoorOpenSkyWeather); outdoor maps keep their scene's and MMerge's fog.
    std::optional<std::array<float, 3>> fogPercent;
};

// The fog levels a daily fog roll picks (weather.yml `open_sky_fog`).
enum class WeatherFogLevel : uint8_t
{
    None = 0,
    Small = 1,
    Average = 2,
    Dense = 3,
};

constexpr std::array<float, 3> DefaultRainColor = {0.7f, 0.76f, 0.84f};

// How one kind of falling flake looks and moves (weather.yml flakes). The defaults are the engine's snow.
struct WeatherFlakeLook
{
    // Linear colour before the sky light; above 1 reads brighter than the fog behind it.
    std::array<float, 3> color = {1.2f, 1.22f, 1.26f};
    // World units per second.
    float fallSpeed = 150.0f;
    // Near and far layer: flake radius and opacity.
    std::array<float, 2> size = {3.0f, 6.0f};
    std::array<float, 2> alpha = {0.9f, 0.75f};
    float sway = 30.0f;
    float swayRate = 1.1f;
    // Weak and strong fog distances the haze closes to at full strength; a strong distance of 0 is no haze.
    std::array<float, 2> haze = {0.0f, 0.0f};
};

// One weather sound: asset paths (one-shots pick one at random) and a volume that levels it with the others.
struct WeatherSound
{
    std::vector<std::string> files;
    float volume = 1.0f;
};

struct WeatherSounds
{
    WeatherSound rainLight;
    WeatherSound rainHeavy;
    WeatherSound wind;
    WeatherSound thunderNear;
    WeatherSound thunderMiddle;
    WeatherSound thunderFar;
};

// engine/rendering/weather/weather.yml. Defaults match the shipped file.
struct WeatherRules
{
    float rainChancePercent = 20.0f;
    float snowChancePercent = 15.0f;
    std::array<float, 12> rainMonthMultipliers = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    std::array<float, 12> snowMonthMultipliers = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    std::unordered_map<std::string, WeatherMapChances> maps;
    std::vector<WeatherIntensityLevel> intensities = {{"light", 0.25f, 30.0f}, {"medium", 0.5f, 40.0f},
        {"heavy", 0.8f, 20.0f}, {"very_heavy", 1.0f, 10.0f}};
    WeatherSpellShape rain = {};
    WeatherSpellShape snow = {180.0f, 720.0f, {30.0f, 80.0f}, {40.0f, 120.0f}};
    WeatherSpellShape ash = {240.0f, 900.0f, {40.0f, 90.0f}, {60.0f, 150.0f}};
    float cloudLeadMinutes = 60.0f;
    float cloudLingerMinutes = 75.0f;
    float variationAmount = 0.25f;
    std::array<float, 2> variationPeriodMinutes = {35.0f, 80.0f};
    float eventIntensity = 0.55f;
    float stormThreshold = 0.72f;
    std::array<float, 2> strikeIntervalSeconds = {6.0f, 22.0f};
    float wetMinutes = 40.0f;
    float dryMinutes = 180.0f;
    std::array<float, 2> calmWind = {30.0f, 160.0f};
    float rainWind = 320.0f;
    float snowWind = 280.0f;
    float ashWind = 220.0f;
    std::array<float, 2> gustRange = {0.6f, 1.6f};
    float fadeSeconds = 40.0f;
    WeatherSounds sounds = {};
    WeatherFlakeLook snowFlakes = {};
    WeatherFlakeLook ashFlakes = {{0.58f, 0.56f, 0.6f}, 55.0f, {2.4f, 4.8f}, {0.85f, 0.7f}, 55.0f, 0.55f,
        {2500.0f, 12000.0f}};
    // flakes beside snow and ash (e.g. ember): looks a map's ash_look names, each starting from the ash look.
    std::unordered_map<std::string, WeatherFlakeLook> namedFlakes;
    // An open sky's small, average and dense fog as a linear fade into the fog colour: [near, far] world units.
    std::array<std::array<float, 2>, 3> openSkyFog = {{{3072.0f, 14336.0f}, {1024.0f, 8192.0f}, {0.0f, 4096.0f}}};

    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    // A named intensity level ("light", "medium", "heavy", "very_heavy"), if defined.
    std::optional<float> namedIntensity(const std::string &name) const;
};

// Weather rules resolved for one map: whether it can rain, snow or fall ash and the base daily chances.
struct WeatherMapSettings
{
    uint32_t mapId = 0;
    bool rainEnabled = false;
    bool snowEnabled = false;
    float rainChancePercent = 0.0f;
    float snowChancePercent = 0.0f;
    // Ash is enabled by its own weather.yml map entry, independent of bolster_maps.txt.
    bool ashEnabled = false;
    float ashChancePercent = 0.0f;
    // The map's own ash look (weather.yml ash_look); unset: the rules' ash flakes.
    std::optional<WeatherFlakeLook> ashLook;
    float dryLightningPercent = 0.0f;
    std::array<float, 3> rainColor = DefaultRainColor;
    // Rain or snow all the time at this peak (weather.yml always), none: the daily rolls.
    PrecipitationKind always = PrecipitationKind::None;
    float alwaysPeak = 0.5f;
    // Daily chances of small, average and dense fog (percent; weather.yml fog).
    std::array<float, 3> fogChancePercent = {};
};

WeatherMapSettings resolveWeatherMapSettings(const WeatherRules &rules, uint32_t mapId,
    const std::string &mapFileName, bool rainEnabled, bool snowEnabled);

// One day's rolled weather: an optional rain, snow or ash spell starting that day, plus the day's calm wind.
struct WeatherDayPlan
{
    PrecipitationKind kind = PrecipitationKind::None;
    float startMinute = 0.0f;
    float durationMinutes = 0.0f;
    float rampUpMinutes = 30.0f;
    float rampDownMinutes = 30.0f;
    float peak = 0.0f;
    float variationPeriodMinutes = 60.0f;
    float variationPhase = 0.0f;
    float windDirectionRadians = 0.0f;
    float calmWindSpeed = 0.0f;
    // A day of dry lightning (weather.yml dry_lightning).
    bool dryLightning = false;
};

// Everything the world shows of the weather at one moment. Wind is in world units per second.
struct WeatherSample
{
    PrecipitationKind precipitation = PrecipitationKind::None;
    float intensity = 0.0f;
    float cloudCover = 0.0f;
    float windX = 0.0f;
    float windY = 0.0f;
    bool storm = false;
    // Lightning without rain (a dry-lightning day while it does not rain).
    bool dryLightning = false;
    float wetness = 0.0f;
};

int weatherDayIndex(double gameMinutes);
// 1-12, matching the calendar's 28-day months.
int weatherMonthForDay(int dayIndex);

// Deterministic for (map, day): the same day always rolls the same weather on every platform.
WeatherDayPlan planWeatherDay(const WeatherRules &rules, const WeatherMapSettings &settings, int dayIndex);
// Rolled weather at a game time without wetness; spells may run across midnight.
WeatherSample sampleRolledWeather(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes);
// Surface wetness from the rain over the preceding hours.
float sampleWetness(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes);
WeatherSample sampleWeather(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes);

// MMerge clear-to-storm sky ladder position for a dry-day roll, raised by clouds and precipitation.
int weatherLadderState(int dryState, int stateCount, const WeatherSample &sample, float stormThreshold);
// Continuous ladder position for MMerge fog distances, so fog thickens smoothly as rain builds.
float weatherFogLadderPosition(int dryState, int stateCount, const WeatherSample &sample, float stormThreshold);
// The look of falling flakes of a kind (snow or ash, the map's own ash look when it has one), or nothing for rain and
// dry weather.
const WeatherFlakeLook *weatherFlakeLook(
    const WeatherRules &rules, PrecipitationKind kind, const WeatherMapSettings *pSettings = nullptr);

struct WeatherFogDistances
{
    bool foggy = false;
    int32_t weakDistance = 0;
    int32_t strongDistance = 0;
};

// The fog level a day rolls (weather.yml fog chances). A fog day runs from 3 am to 3 am, as an outdoor map's daily fog.
WeatherFogLevel rollDailyFog(const WeatherMapSettings &settings, int fogDayIndex);
int weatherFogDayIndex(double gameMinutes);

// An open sky's fog at a moment as a linear fade [near, far]: the day's level (open_sky_fog), blended from the day
// before's over the first hour after 3 am. Not foggy on a clear day.
struct WeatherOpenSkyFog
{
    bool foggy = false;
    float nearDistance = 0.0f;
    float farDistance = 0.0f;
};

WeatherOpenSkyFog sampleOpenSkyFog(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes,
    std::optional<WeatherFogLevel> forcedLevel = std::nullopt);

// MMerge ladder fog (8192 / position, 16192 / position above a third of the ladder), faded in over one ladder step.
WeatherFogDistances weatherLadderFog(float position, int stateCount);
// Fog closing in with falling flakes that have a haze (ash): from distant at a trace to the look's haze distances
// at full strength. Not foggy when the sample has no haze.
WeatherFogDistances weatherPrecipitationHaze(
    const WeatherRules &rules, const WeatherSample &sample, const WeatherMapSettings *pSettings = nullptr);
}
