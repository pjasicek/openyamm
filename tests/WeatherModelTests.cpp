#include "doctest/doctest.h"

#include "game/outdoor/WeatherModel.h"
#include "game/outdoor/WeatherPresentation.h"
#include "game/render/WeatherRoofMap.h"

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

TEST_CASE("weather flake looks keep the engine's snow and the repository's ash")
{
    const WeatherRules rules = loadRepositoryRules();
    const WeatherFlakeLook engineSnow;
    const WeatherRules defaults;
    // The repository file restates the snow the engine always drew, exactly.
    CHECK(rules.snowFlakes.color == engineSnow.color);
    CHECK(rules.snowFlakes.fallSpeed == engineSnow.fallSpeed);
    CHECK(rules.snowFlakes.size == engineSnow.size);
    CHECK(rules.snowFlakes.alpha == engineSnow.alpha);
    CHECK(rules.snowFlakes.sway == engineSnow.sway);
    CHECK(rules.snowFlakes.swayRate == engineSnow.swayRate);
    CHECK(rules.snowFlakes.haze[1] == 0.0f);
    CHECK(rules.ashFlakes.color == defaults.ashFlakes.color);
    CHECK(rules.ashFlakes.fallSpeed == defaults.ashFlakes.fallSpeed);
    CHECK(rules.ashFlakes.haze == defaults.ashFlakes.haze);
    CHECK(rules.ashWind == defaults.ashWind);
    CHECK(rules.ashFlakes.fallSpeed < rules.snowFlakes.fallSpeed);
    CHECK(weatherFlakeLook(rules, PrecipitationKind::Rain) == nullptr);
    CHECK(weatherFlakeLook(rules, PrecipitationKind::Ash) == &rules.ashFlakes);

    WeatherRules partial;
    std::string errorMessage;
    REQUIRE_MESSAGE(partial.loadFromYaml("version: 1\nflakes:\n  ash: {fall_speed: 40}\n", errorMessage),
        errorMessage);
    CHECK(partial.ashFlakes.fallSpeed == doctest::Approx(40.0f));
    CHECK(partial.ashFlakes.color == defaults.ashFlakes.color);
    CHECK(partial.snowFlakes.fallSpeed == engineSnow.fallSpeed);
    CHECK_FALSE(partial.loadFromYaml("version: 1\nflakes:\n  ash: {haze: [9000, 100]}\n", errorMessage));
    // Other keys are named looks (ember), checked as the ash look is.
    CHECK_FALSE(partial.loadFromYaml("version: 1\nflakes:\n  hail: {glow: 1}\n", errorMessage));
}

TEST_CASE("ash falls only on maps weather.yml gives it and leaves every other roll unchanged")
{
    WeatherRules rules = loadRepositoryRules();
    std::string errorMessage;
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rendering/weather/weather.yml");
    std::stringstream contents;
    contents << file.rdbuf() << "\n";
    std::string text = contents.str();
    // The test map's entry is appended to the repository's maps.
    const size_t mapsAt = text.find("\nmaps:\n");
    REQUIRE(mapsAt != std::string::npos);
    text.insert(mapsAt + 7, "  ashland.odm: {ash: 60}\n");
    REQUIRE_MESSAGE(rules.loadFromYaml(text, errorMessage), errorMessage);

    // No repository map has ash.
    for (const char *pMap : {"oute3.odm", "7out13.odm", "outb1.odm", "out01.odm"})
    {
        CHECK_FALSE(resolveWeatherMapSettings(rules, 1, pMap, true, true).ashEnabled);
    }

    const WeatherMapSettings ashland = resolveWeatherMapSettings(rules, 63, "AshLand.odm", true, true);
    REQUIRE(ashland.ashEnabled);
    CHECK(ashland.ashChancePercent == doctest::Approx(60.0f));
    WeatherMapSettings withoutAsh = ashland;
    withoutAsh.ashEnabled = false;
    int ashDays = 0;
    int summerAshDays = 0;

    for (int day = 0; day < 336 * 2; ++day)
    {
        const WeatherDayPlan plan = planWeatherDay(rules, ashland, day);
        const WeatherDayPlan before = planWeatherDay(rules, withoutAsh, day);
        CHECK(plan.windDirectionRadians == before.windDirectionRadians);
        CHECK(plan.calmWindSpeed == before.calmWindSpeed);

        if (before.kind != PrecipitationKind::None)
        {
            // Rain and snow days are exactly what they were without ash.
            CHECK(plan.kind == before.kind);
            CHECK(plan.startMinute == before.startMinute);
            CHECK(plan.durationMinutes == before.durationMinutes);
            CHECK(plan.peak == before.peak);
        }
        else if (plan.kind == PrecipitationKind::Ash)
        {
            ++ashDays;
            const int month = weatherMonthForDay(day);
            summerAshDays += month >= 6 && month <= 8 ? 1 : 0;
            CHECK(plan.durationMinutes >= rules.ash.minMinutes);
            CHECK(plan.durationMinutes <= rules.ash.maxMinutes);
        }
    }

    CHECK(ashDays > 100);
    // Not seasonal.
    CHECK(summerAshDays > 10);

    // An ash-only map (no bolster row: rain and snow disabled).
    const WeatherMapSettings ashOnly = resolveWeatherMapSettings(rules, 9101, "ashland.odm", false, false);
    const int day = findDay(rules, ashOnly, PrecipitationKind::Ash);
    const WeatherDayPlan plan = planWeatherDay(rules, ashOnly, day);
    const double middle = day * MinutesPerDay + plan.startMinute + plan.durationMinutes * 0.5;
    const WeatherSample sample = sampleWeather(rules, ashOnly, middle);
    CHECK(sample.precipitation == PrecipitationKind::Ash);
    CHECK(sample.intensity > 0.0f);
    CHECK_FALSE(sample.storm);
    CHECK(sample.wetness == 0.0f);
    CHECK(std::hypot(sample.windX, sample.windY) > plan.calmWindSpeed);

    // Ash brings its haze; rain and snow bring none, and the ladder's rain skies stay with rain.
    const WeatherFogDistances haze = weatherPrecipitationHaze(rules, sample);
    CHECK(haze.foggy);
    CHECK(haze.strongDistance > haze.weakDistance);
    WeatherSample full = sample;
    full.intensity = 1.0f;
    CHECK(weatherPrecipitationHaze(rules, full).strongDistance
        == static_cast<int32_t>(rules.ashFlakes.haze[1]));
    WeatherSample snow = full;
    snow.precipitation = PrecipitationKind::Snow;
    CHECK_FALSE(weatherPrecipitationHaze(rules, snow).foggy);
    full.cloudCover = 0.0f;
    CHECK(weatherLadderState(0, 7, full, rules.stormThreshold) == 0);
}

TEST_CASE("weather presentation fades ash without overlapping snow")
{
    const WeatherRules rules = loadRepositoryRules();
    WeatherPresentation presentation;
    WeatherSample snow;
    snow.precipitation = PrecipitationKind::Snow;
    snow.intensity = 0.6f;
    presentation.update(rules, snow, 0.016f);
    WeatherSample ash;
    ash.precipitation = PrecipitationKind::Ash;
    ash.intensity = 0.7f;

    for (int frame = 0; frame < 60 * 120; ++frame)
    {
        presentation.update(rules, ash, 1.0f / 60.0f);
        CHECK((presentation.snowLevel() == 0.0f || presentation.ashLevel() == 0.0f));
        CHECK(presentation.rainLevel() == 0.0f);
    }

    CHECK(presentation.snowLevel() == 0.0f);
    CHECK(presentation.ashLevel() == doctest::Approx(0.7f));
    CHECK_FALSE(presentation.storm());
}

TEST_CASE("a map's weather entry gives dry lightning days, its own ash look and its rain colour")
{
    WeatherRules rules;
    std::string errorMessage;
    REQUIRE_MESSAGE(rules.loadFromYaml("version: 1\n"
        "flakes:\n  ash: {fall_speed: 50}\n  ember: {color: [1.6, 0.6, 0.2], haze: none}\n"
        "maps:\n  crown.odm: {dry_lightning: 100}\n  scour.odm: {ash: 50, ash_look: ember}\n"
        "  brood.odm: {rain_color: [0.6, 0.85, 0.4]}\n", errorMessage), errorMessage);

    // A named look starts from the ash look.
    REQUIRE(rules.namedFlakes.contains("ember"));
    CHECK(rules.namedFlakes.at("ember").fallSpeed == doctest::Approx(50.0f));
    CHECK(rules.namedFlakes.at("ember").color[0] == doctest::Approx(1.6f));

    const WeatherMapSettings scour = resolveWeatherMapSettings(rules, 2, "scour.odm", false, false);
    REQUIRE(scour.ashLook.has_value());
    CHECK(weatherFlakeLook(rules, PrecipitationKind::Ash, &scour) == &*scour.ashLook);
    CHECK(weatherFlakeLook(rules, PrecipitationKind::Ash) == &rules.ashFlakes);
    WeatherSample ashFall;
    ashFall.precipitation = PrecipitationKind::Ash;
    ashFall.intensity = 1.0f;
    CHECK(weatherPrecipitationHaze(rules, ashFall).foggy);
    CHECK_FALSE(weatherPrecipitationHaze(rules, ashFall, &scour).foggy);

    const WeatherMapSettings brood = resolveWeatherMapSettings(rules, 3, "brood.odm", true, false);
    CHECK(brood.rainColor[1] == doctest::Approx(0.85f));
    CHECK(scour.rainColor == DefaultRainColor);

    // Every day of the crown is a dry-lightning day; no other map has one, and the other rolls are unchanged.
    const WeatherMapSettings crown = resolveWeatherMapSettings(rules, 4, "crown.odm", false, false);
    WeatherMapSettings plain = crown;
    plain.dryLightningPercent = 0.0f;

    for (int day = 0; day < 40; ++day)
    {
        CHECK(planWeatherDay(rules, crown, day).dryLightning);
        CHECK_FALSE(planWeatherDay(rules, plain, day).dryLightning);
        CHECK(planWeatherDay(rules, crown, day).windDirectionRadians
            == planWeatherDay(rules, plain, day).windDirectionRadians);
    }

    CHECK(sampleRolledWeather(rules, crown, 600.0).dryLightning);
    CHECK_FALSE(sampleRolledWeather(rules, scour, 600.0).dryLightning);

    WeatherRules bad;
    CHECK_FALSE(bad.loadFromYaml("version: 1\nmaps:\n  scour.odm: {ash: 50, ash_look: smoke}\n", errorMessage));
    CHECK(errorMessage.find("ash_look names no flakes entry") != std::string::npos);
}

TEST_CASE("weather presentation throws dry lightning without rain, mostly far off")
{
    const WeatherRules rules = loadRepositoryRules();
    WeatherPresentation presentation;
    WeatherSample dry;
    dry.dryLightning = true;
    size_t strikes = 0;
    size_t near = 0;

    for (int frame = 0; frame < 60 * 600; ++frame)
    {
        presentation.update(rules, dry, 1.0f / 60.0f);
        CHECK(presentation.rainLevel() == 0.0f);

        for (const LightningStrike &strike : presentation.takeStrikes())
        {
            ++strikes;
            near += strike.distance == LightningDistance::Near ? 1 : 0;
        }
    }

    CHECK(strikes >= 10);
    CHECK(near * 5 < strikes);
    CHECK_FALSE(presentation.storm());
}

TEST_CASE("a map's always weather rains or snows without a break, only where the map can")
{
    WeatherRules rules;
    std::string errorMessage;
    REQUIRE_MESSAGE(rules.loadFromYaml("version: 1\nmaps:\n  wet.blv: {always: rain, peak: 0.85}\n"
        "  cold.blv: {always: snow, peak: 0.4}\n", errorMessage), errorMessage);
    const WeatherMapSettings wet = resolveWeatherMapSettings(rules, 9001, "wet.blv", true, false);
    const WeatherMapSettings cold = resolveWeatherMapSettings(rules, 9002, "cold.blv", false, true);
    // A kind the map cannot have is ignored: the daily rolls apply.
    const WeatherMapSettings dryCold = resolveWeatherMapSettings(rules, 9003, "cold.blv", true, false);
    CHECK(wet.always == PrecipitationKind::Rain);
    CHECK(cold.always == PrecipitationKind::Snow);
    CHECK(dryCold.always == PrecipitationKind::None);
    bool storm = false;

    // Past the first game day, every minute has it, across midnights, near the peak.
    for (double minute = MinutesPerDay; minute < 6.0 * MinutesPerDay; minute += 7.0)
    {
        const WeatherSample rain = sampleRolledWeather(rules, wet, minute);
        const WeatherSample snow = sampleRolledWeather(rules, cold, minute);
        REQUIRE(rain.precipitation == PrecipitationKind::Rain);
        REQUIRE(snow.precipitation == PrecipitationKind::Snow);
        CHECK(rain.intensity >= 0.85f * (1.0f - rules.variationAmount) - 0.01f);
        CHECK(snow.intensity <= 0.4f * (1.0f + rules.variationAmount) + 0.01f);
        CHECK_FALSE(snow.storm);
        storm = storm || rain.storm;
    }

    CHECK(storm);
    WeatherRules bad;
    CHECK_FALSE(bad.loadFromYaml("version: 1\nmaps:\n  ash.blv: {always: ash}\n", errorMessage));
}

TEST_CASE("an open sky's fog days roll by weather.yml chances and blend in after 3 am")
{
    WeatherRules rules;
    std::string errorMessage;
    REQUIRE_MESSAGE(rules.loadFromYaml("version: 1\nmaps:\n  misty.blv: {fog: [30, 20, 10]}\n"
        "  wet.blv: {always: rain, peak: 0.85, fog: [30, 20, 10]}\n"
        "open_sky_fog: {small: [3000, 14000], average: [1000, 8000], dense: [0, 4000]}\n", errorMessage),
        errorMessage);
    const WeatherMapSettings misty = resolveWeatherMapSettings(rules, 9001, "misty.blv", true, false);
    const WeatherMapSettings clear = resolveWeatherMapSettings(rules, 9002, "clear.blv", true, false);
    CHECK(misty.fogChancePercent[2] == doctest::Approx(10.0f));
    int counts[4] = {};

    for (int day = 0; day < 2000; ++day)
    {
        const WeatherFogLevel level = rollDailyFog(misty, day);
        ++counts[static_cast<size_t>(level)];
        // Deterministic, and never on a map without chances.
        REQUIRE(rollDailyFog(misty, day) == level);
        REQUIRE(rollDailyFog(clear, day) == WeatherFogLevel::None);
    }

    CHECK(counts[1] > 500);
    CHECK(counts[1] < 700);
    CHECK(counts[2] > 330);
    CHECK(counts[2] < 470);
    CHECK(counts[3] > 140);
    CHECK(counts[3] < 260);
    CHECK(counts[0] > 700);

    // Fog does not change a day's rain: the same plans with and without fog chances.
    const WeatherMapSettings wet = resolveWeatherMapSettings(rules, 9001, "wet.blv", true, false);
    WeatherMapSettings wetWithoutFog = wet;
    wetWithoutFog.fogChancePercent = {};

    for (int day = 0; day < 50; ++day)
    {
        CHECK(planWeatherDay(rules, wet, day).peak == planWeatherDay(rules, wetWithoutFog, day).peak);
    }

    // A fog day runs from 3 am to 3 am: the hour before it keeps the day before's.
    CHECK(weatherFogDayIndex(5.0 * MinutesPerDay + 179.0) == 4);
    CHECK(weatherFogDayIndex(5.0 * MinutesPerDay + 180.0) == 5);

    // Find a dense day after a clear one: the fog closes in over the hour after 3 am.
    int denseDay = -1;

    for (int day = 1; day < 2000 && denseDay < 0; ++day)
    {
        if (rollDailyFog(misty, day) == WeatherFogLevel::Dense && rollDailyFog(misty, day - 1) == WeatherFogLevel::None)
        {
            denseDay = day;
        }
    }

    REQUIRE(denseDay > 0);
    const double start = denseDay * MinutesPerDay + 180.0;
    CHECK_FALSE(sampleOpenSkyFog(rules, misty, start - 1.0).foggy);
    const WeatherOpenSkyFog early = sampleOpenSkyFog(rules, misty, start + 10.0);
    const WeatherOpenSkyFog half = sampleOpenSkyFog(rules, misty, start + 30.0);
    const WeatherOpenSkyFog full = sampleOpenSkyFog(rules, misty, start + 60.0);
    CHECK(early.foggy);
    CHECK(early.farDistance > half.farDistance);
    CHECK(half.farDistance > full.farDistance);
    CHECK(full.nearDistance == doctest::Approx(0.0f));
    CHECK(full.farDistance == doctest::Approx(4000.0f));
    CHECK(sampleOpenSkyFog(rules, misty, start + 600.0).farDistance == doctest::Approx(4000.0f));

    // The console's forced level wins; none is clear.
    CHECK(sampleOpenSkyFog(rules, clear, start, WeatherFogLevel::Average).farDistance == doctest::Approx(8000.0f));
    CHECK_FALSE(sampleOpenSkyFog(rules, misty, start + 60.0, WeatherFogLevel::None).foggy);

    WeatherRules bad;
    CHECK_FALSE(bad.loadFromYaml("version: 1\nmaps:\n  a.blv: {fog: [60, 30, 20]}\n", errorMessage));
    CHECK_FALSE(bad.loadFromYaml("version: 1\nmaps:\n  a.blv: {fog: [10, 5]}\n", errorMessage));
    CHECK_FALSE(bad.loadFromYaml("version: 1\nopen_sky_fog: {dense: [4000, 0]}\n", errorMessage));
}

TEST_CASE("weather roof map: rain stops at the highest surface seen from the sky")
{
    WeatherRoofMap roofMap;
    roofMap.reset(0.0f, 0.0f, 1000.0f, 1000.0f, 64.0f, 1024);
    REQUIRE_FALSE(roofMap.empty());
    // Ground at 0 everywhere, a flat roof at 300 over 200-400, and a wall (no area from above) that changes nothing.
    roofMap.addTriangle({0.0f, 0.0f, 0.0f}, {1000.0f, 0.0f, 0.0f}, {1000.0f, 1000.0f, 0.0f});
    roofMap.addTriangle({0.0f, 0.0f, 0.0f}, {1000.0f, 1000.0f, 0.0f}, {0.0f, 1000.0f, 0.0f});
    roofMap.addTriangle({200.0f, 200.0f, 300.0f}, {400.0f, 200.0f, 300.0f}, {400.0f, 400.0f, 300.0f});
    roofMap.addTriangle({200.0f, 200.0f, 300.0f}, {400.0f, 400.0f, 300.0f}, {200.0f, 400.0f, 300.0f});
    roofMap.addTriangle({600.0f, 600.0f, 0.0f}, {600.0f, 800.0f, 0.0f}, {600.0f, 800.0f, 900.0f});

    CHECK(roofMap.heightAt(300.0f, 300.0f) == doctest::Approx(300.0f));
    CHECK(roofMap.heightAt(700.0f, 700.0f) == doctest::Approx(0.0f));
    CHECK(roofMap.heightAt(600.0f, 700.0f) == doctest::Approx(0.0f));
    // Under the roof is covered, on it or in the open is not; off the map there is no surface.
    CHECK(roofMap.covers(300.0f, 300.0f, 100.0f, 16.0f));
    CHECK_FALSE(roofMap.covers(300.0f, 300.0f, 350.0f, 16.0f));
    CHECK_FALSE(roofMap.covers(700.0f, 700.0f, 100.0f, 16.0f));
    CHECK(roofMap.heightAt(-50.0f, 300.0f) == WeatherRoofMap::NoSurface);
    // A sloped roof: the height follows the slope.
    roofMap.addTriangle({600.0f, 100.0f, 200.0f}, {900.0f, 100.0f, 500.0f}, {900.0f, 400.0f, 500.0f});
    CHECK(roofMap.heightAt(860.0f, 140.0f) == doctest::Approx(200.0f + (864.0f - 600.0f)).epsilon(0.02));

    // A large map grows its cells to stay within the cell limit.
    WeatherRoofMap large;
    large.reset(-32000.0f, -32000.0f, 32000.0f, 32000.0f, 16.0f, 512);
    CHECK(large.width() <= 512);
    CHECK(large.cellSize() >= 125.0f);
}
