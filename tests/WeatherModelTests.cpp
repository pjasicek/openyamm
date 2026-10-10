#include "doctest/doctest.h"

#include "game/outdoor/WeatherModel.h"
#include "game/outdoor/WeatherPresentation.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
constexpr double MinutesPerDay = 1440.0;

WeatherRules loadRepositoryRules()
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rendering/weather/weather.yml");
    std::stringstream contents;
    contents << file.rdbuf();
    WeatherRules rules;
    std::string errorMessage;
    REQUIRE_MESSAGE(rules.loadFromYaml(contents.str(), errorMessage), errorMessage);
    return rules;
}

WeatherMapSettings rainySnowyMap(const WeatherRules &rules)
{
    return resolveWeatherMapSettings(rules, 63, "7out02.odm", true, true);
}

// First day at or after `firstDay` whose roll has the given precipitation.
int findDay(const WeatherRules &rules, const WeatherMapSettings &settings, PrecipitationKind kind, int firstDay = 0)
{
    for (int day = firstDay; day < firstDay + 4000; ++day)
    {
        if (planWeatherDay(rules, settings, day).kind == kind)
        {
            return day;
        }
    }

    FAIL("no day with the requested weather");
    return -1;
}
}

TEST_CASE("weather repository rules load with per-map chances and named intensities")
{
    const WeatherRules rules = loadRepositoryRules();
    CHECK(rules.rainChancePercent == doctest::Approx(20.0f));
    CHECK(rules.snowMonthMultipliers[6] == doctest::Approx(0.0f));
    CHECK(rules.namedIntensity("heavy").value_or(0.0f) == doctest::Approx(0.8f));
    CHECK_FALSE(rules.namedIntensity("drizzle").has_value());

    const WeatherMapSettings tatalia = resolveWeatherMapSettings(rules, 72, "7OUT13.ODM", true, false);
    CHECK(tatalia.rainChancePercent == doctest::Approx(30.0f));
    CHECK(tatalia.snowChancePercent == doctest::Approx(rules.snowChancePercent));
    const WeatherMapSettings other = resolveWeatherMapSettings(rules, 2, "out02.odm", true, false);
    CHECK(other.rainChancePercent == doctest::Approx(rules.rainChancePercent));
}

TEST_CASE("weather repository sounds name existing engine audio files")
{
    const WeatherRules rules = loadRepositoryRules();
    const std::filesystem::path assets = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";

    for (const WeatherSound *pSound : {&rules.sounds.rainLight, &rules.sounds.rainHeavy, &rules.sounds.wind,
             &rules.sounds.thunderNear, &rules.sounds.thunderMiddle, &rules.sounds.thunderFar})
    {
        REQUIRE_FALSE(pSound->files.empty());
        CHECK(pSound->volume > 0.0f);

        for (const std::string &file : pSound->files)
        {
            CHECK_MESSAGE(file.rfind("engine/", 0) == 0, file);
            CHECK_MESSAGE(std::filesystem::is_regular_file(assets / file), file);
        }
    }

    CHECK(rules.sounds.thunderNear.files.size() > 1);
}

TEST_CASE("weather rules reject unknown keys and bad ranges")
{
    WeatherRules rules;
    std::string errorMessage;
    CHECK_FALSE(rules.loadFromYaml("version: 1\nchances: {rain: 20, hail: 3}\n", errorMessage));
    CHECK(errorMessage.find("hail") != std::string::npos);
    CHECK_FALSE(rules.loadFromYaml("version: 1\nwind: {calm: [200, 100]}\n", errorMessage));
    CHECK_FALSE(rules.loadFromYaml("version: 2\n", errorMessage));
    CHECK_FALSE(rules.loadFromYaml("version: 1\nsounds: {wind: {volume: 0.5}}\n", errorMessage));
    CHECK(rules.loadFromYaml("version: 1\nchances: {rain: 50}\n", errorMessage));
    CHECK(rules.rainChancePercent == doctest::Approx(50.0f));
}

TEST_CASE("weather days roll deterministically and respect the map's enabled kinds")
{
    const WeatherRules rules = loadRepositoryRules();
    const WeatherMapSettings settings = rainySnowyMap(rules);
    int rainDays = 0;
    int snowDays = 0;

    for (int day = 0; day < 336 * 4; ++day)
    {
        const WeatherDayPlan first = planWeatherDay(rules, settings, day);
        const WeatherDayPlan second = planWeatherDay(rules, settings, day);
        CHECK(first.kind == second.kind);
        CHECK(first.startMinute == second.startMinute);
        CHECK(first.peak == second.peak);
        rainDays += first.kind == PrecipitationKind::Rain ? 1 : 0;
        snowDays += first.kind == PrecipitationKind::Snow ? 1 : 0;

        if (first.kind == PrecipitationKind::Snow)
        {
            // No snow in the summer months.
            const int month = weatherMonthForDay(day);
            CHECK((month < 6 || month > 8));
        }
    }

    CHECK(rainDays > 100);
    CHECK(snowDays > 40);

    WeatherMapSettings dryMap = settings;
    dryMap.rainEnabled = false;
    dryMap.snowEnabled = false;

    for (int day = 0; day < 200; ++day)
    {
        CHECK(planWeatherDay(rules, dryMap, day).kind == PrecipitationKind::None);
    }
}

TEST_CASE("weather intensity ramps smoothly through a spell and across midnight")
{
    const WeatherRules rules = loadRepositoryRules();
    const WeatherMapSettings settings = rainySnowyMap(rules);
    const int day = findDay(rules, settings, PrecipitationKind::Rain, 30);
    const WeatherDayPlan plan = planWeatherDay(rules, settings, day);
    const double spellStart = day * MinutesPerDay + plan.startMinute;
    float previous = sampleRolledWeather(rules, settings, spellStart - 1.0).intensity;
    float peak = 0.0f;

    for (double minute = spellStart - 1.0; minute < spellStart + plan.durationMinutes + 30.0; minute += 0.5)
    {
        const float intensity = sampleRolledWeather(rules, settings, minute).intensity;
        // Half a game minute is one real second: no visible jumps.
        CHECK(std::abs(intensity - previous) < 0.05f);
        previous = intensity;
        peak = std::max(peak, intensity);
    }

    CHECK(peak > plan.peak * 0.7f);
    CHECK(sampleRolledWeather(rules, settings, spellStart + plan.durationMinutes + 1.0).intensity == 0.0f);

    // Clouds gather before the first drops.
    const WeatherSample beforeRain = sampleRolledWeather(rules, settings, spellStart - 10.0);
    CHECK(beforeRain.intensity == 0.0f);
    CHECK(beforeRain.cloudCover > 0.3f);

    // Wind and clouds stay continuous over every midnight of a year.
    for (int boundary = 1; boundary < 336; ++boundary)
    {
        const WeatherSample before = sampleRolledWeather(rules, settings, boundary * MinutesPerDay - 0.25);
        const WeatherSample after = sampleRolledWeather(rules, settings, boundary * MinutesPerDay + 0.25);
        CHECK(std::abs(before.intensity - after.intensity) < 0.05f);
        CHECK(std::abs(before.cloudCover - after.cloudCover) < 0.05f);
        CHECK(std::abs(before.windX - after.windX) < 5.0f);
        CHECK(std::abs(before.windY - after.windY) < 5.0f);
    }
}

TEST_CASE("weather storms need heavy rain and surfaces stay wet after rain")
{
    const WeatherRules rules = loadRepositoryRules();
    const WeatherMapSettings settings = rainySnowyMap(rules);
    bool sawStorm = false;

    for (int day = 0; day < 600 && !sawStorm; ++day)
    {
        for (int minute = 0; minute < 1440; minute += 10)
        {
            const WeatherSample sample = sampleRolledWeather(rules, settings, day * MinutesPerDay + minute);
            CHECK(sample.storm == (sample.precipitation == PrecipitationKind::Rain
                && sample.intensity >= rules.stormThreshold));
            sawStorm = sawStorm || sample.storm;
        }
    }

    CHECK(sawStorm);

    const int day = findDay(rules, settings, PrecipitationKind::Rain, 50);
    const WeatherDayPlan plan = planWeatherDay(rules, settings, day);
    const double spellEnd = day * MinutesPerDay + plan.startMinute + plan.durationMinutes;
    CHECK(sampleWetness(rules, settings, spellEnd - plan.rampDownMinutes) > 0.5f);
    const float justAfter = sampleWetness(rules, settings, spellEnd + 10.0);
    const float later = sampleWetness(rules, settings, spellEnd + rules.dryMinutes * 0.5);
    CHECK(justAfter > later);
    CHECK(sampleWetness(rules, settings, spellEnd + rules.dryMinutes + 60.0) < justAfter);
}

TEST_CASE("weather ladder keeps dry days below rain and follows precipitation")
{
    WeatherSample dry;
    CHECK(weatherLadderState(6, 7, dry, 0.72f) == 3);
    CHECK(weatherLadderState(1, 7, dry, 0.72f) == 1);

    WeatherSample cloudy;
    cloudy.cloudCover = 0.7f;
    CHECK(weatherLadderState(0, 7, cloudy, 0.72f) == 3);

    WeatherSample rain;
    rain.precipitation = PrecipitationKind::Rain;
    rain.intensity = 0.5f;
    rain.cloudCover = 0.8f;
    CHECK(weatherLadderState(0, 7, rain, 0.72f) == 4);

    WeatherSample storm = rain;
    storm.intensity = 0.9f;
    storm.storm = true;
    CHECK(weatherLadderState(0, 7, storm, 0.72f) == 5);

    // Fog thickens continuously as the rain builds.
    float previousStrong = 1.0e9f;

    for (float intensity = 0.0f; intensity <= 1.0f; intensity += 0.05f)
    {
        WeatherSample sample = rain;
        sample.intensity = intensity;
        const WeatherFogDistances fog = weatherLadderFog(weatherFogLadderPosition(0, 7, sample, 0.72f), 7);
        REQUIRE(fog.foggy);
        CHECK(static_cast<float>(fog.strongDistance) <= previousStrong);
        CHECK(fog.weakDistance < fog.strongDistance);
        previousStrong = static_cast<float>(fog.strongDistance);
    }

    CHECK_FALSE(weatherLadderFog(2.0f, 7).foggy);
    CHECK(weatherLadderFog(3.0f, 7).strongDistance == 16192 / 3);
}

TEST_CASE("weather presentation fades precipitation and never overlaps rain and snow")
{
    const WeatherRules rules = loadRepositoryRules();
    WeatherPresentation presentation;
    WeatherSample rain;
    rain.precipitation = PrecipitationKind::Rain;
    rain.intensity = 0.8f;
    presentation.update(rules, rain, 0.016f);
    // The first update snaps.
    CHECK(presentation.rainLevel() == doctest::Approx(0.8f));

    WeatherSample snow;
    snow.precipitation = PrecipitationKind::Snow;
    snow.intensity = 0.5f;

    for (int frame = 0; frame < 60 * 120; ++frame)
    {
        presentation.update(rules, snow, 1.0f / 60.0f);
        CHECK((presentation.rainLevel() == 0.0f || presentation.snowLevel() == 0.0f));
    }

    CHECK(presentation.rainLevel() == 0.0f);
    CHECK(presentation.snowLevel() == doctest::Approx(0.5f));

    // A full fade takes fade_seconds.
    presentation.update(rules, WeatherSample{}, rules.fadeSeconds * 0.25f);
    CHECK(presentation.snowLevel() == doctest::Approx(0.25f));
    presentation.snap();
    presentation.update(rules, rain, 0.0f);
    CHECK(presentation.rainLevel() == doctest::Approx(0.8f));
}

TEST_CASE("weather presentation throws lightning in storms with thunder delayed by distance")
{
    const WeatherRules rules = loadRepositoryRules();
    WeatherPresentation presentation;
    WeatherSample storm;
    storm.precipitation = PrecipitationKind::Rain;
    storm.intensity = 1.0f;
    storm.storm = true;
    float flashPeak = 0.0f;
    size_t strikes = 0;

    for (int frame = 0; frame < 60 * 120; ++frame)
    {
        presentation.update(rules, storm, 1.0f / 60.0f);
        flashPeak = std::max(flashPeak, presentation.lightningFlash());

        for (const LightningStrike &strike : presentation.takeStrikes())
        {
            CHECK(strike.thunderDelaySeconds > 0.5f);
            CHECK(strike.thunderDelaySeconds < 20.0f);
            ++strikes;
        }
    }

    CHECK(strikes >= 4);
    CHECK(flashPeak > 0.3f);

    WeatherPresentation calm;
    WeatherSample rain = storm;
    rain.storm = false;

    for (int frame = 0; frame < 60 * 60; ++frame)
    {
        calm.update(rules, rain, 1.0f / 60.0f);
        CHECK(calm.lightningFlash() == 0.0f);
    }

    CHECK(calm.takeStrikes().empty());
    calm.forceStrike(LightningDistance::Near);
    const std::vector<LightningStrike> forced = calm.takeStrikes();
    REQUIRE(forced.size() == 1);
    CHECK(forced[0].distance == LightningDistance::Near);
    CHECK(forced[0].thunderDelaySeconds < 3.0f);
}
