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
    std::array<float, 2> gustRange = {0.6f, 1.6f};
    float fadeSeconds = 40.0f;
    WeatherSounds sounds = {};

    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    // A named intensity level ("light", "medium", "heavy", "very_heavy"), if defined.
    std::optional<float> namedIntensity(const std::string &name) const;
};

// Weather rules resolved for one map: whether it can rain or snow and the base daily chances.
struct WeatherMapSettings
{
    uint32_t mapId = 0;
    bool rainEnabled = false;
    bool snowEnabled = false;
    float rainChancePercent = 0.0f;
    float snowChancePercent = 0.0f;
};

WeatherMapSettings resolveWeatherMapSettings(const WeatherRules &rules, uint32_t mapId,
    const std::string &mapFileName, bool rainEnabled, bool snowEnabled);

// One day's rolled weather: an optional rain or snow spell starting that day, plus the day's calm wind.
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

struct WeatherFogDistances
{
    bool foggy = false;
    int32_t weakDistance = 0;
    int32_t strongDistance = 0;
};

// MMerge ladder fog (8192 / position, 16192 / position above a third of the ladder), faded in over one ladder step.
WeatherFogDistances weatherLadderFog(float position, int stateCount);
}
