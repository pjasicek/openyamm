#include "doctest/doctest.h"

#include "game/StringUtils.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorDistantSea.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/render/SkyClock.h"
#include "game/render/SkyPresets.h"
#include "game/render/SkyState.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::string readSourceFile(const std::string &relativePath)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::stringstream contents;
    contents << file.rdbuf();
    return contents.str();
}

SkyPresetLibrary loadRepositoryLibrary()
{
    SkyPresetLibrary library;
    std::string error;
    const bool loaded = library.loadFromYaml(readSourceFile("assets_dev/engine/rendering/sky/sky.yml"), error);
    INFO(error);
    REQUIRE(loaded);
    return library;
}

std::vector<std::string> splitTabs(const std::string &line)
{
    std::vector<std::string> columns;
    std::stringstream stream(line);
    std::string column;

    while (std::getline(stream, column, '\t'))
    {
        columns.push_back(column);
    }

    return columns;
}

std::string trimmed(const std::string &value)
{
    const size_t begin = value.find_first_not_of(" \r\"");
    const size_t end = value.find_last_not_of(" \r\"");
    return begin == std::string::npos ? std::string() : value.substr(begin, end - begin + 1);
}

// Minimal library: one fully keyed parent and a child overriding one track.
const char *TestLibraryYaml = R"(
version: 1
transition_seconds: 10
fallback: day
special: {underwater: deep, red_fog: hot, rain: wet}
weather_ladder: [day, wet, stormy]
aliases: {sky05: day, STORMCLDS: stormy}
presets:
  day:
    keys:
      - {time: "06:00", zenith: [0, 0, 0], horizon: [0, 0, 0], horizon_exponent: 3, sun_glow: [1, 1, 1],
         sun_glow_exponent: 8, sun_glow_strength: 0, fog: [0.5, 0.5, 0.5], sun_disc: [1, 1, 1],
         sun_disc_visibility: 1, cloud_lit: [1, 1, 1], cloud_shadow: [0.5, 0.5, 0.5], ambient_tint: [1, 1, 1],
         water_sun: [1, 1, 1], water_sky: [0.3, 0.4, 0.5], stars: 0, moon_visibility: 0,
         aerial_haze: 0.8}
      - {time: "18:00", zenith: [1, 1, 1], horizon: [1, 1, 1], stars: 1}
    clouds:
      - {texture: clouds_cumulus, coverage: 0.3, speed: 0.01, direction_deg: 0}
  wet:
    inherits: day
    keys:
      - {time: "12:00", zenith: [0.2, 0.2, 0.2]}
    clouds:
      - {texture: clouds_cumulus, coverage: 0.9, speed: 0.01, direction_deg: 0}
      - {texture: legacy/storm_painting, mode: color}
  stormy:
    inherits: wet
    storm: true
    moon_texture: broken_moon
    moon_phase_offset: 0.5
  hot:
    inherits: day
  deep:
    inherits: day
    draw_sky: false
themes:
  ember: {sky_tint: [2, 1, 0.5], sun_tint: [1, 0.5, 0.5], saturation: 0.5, haze: 0.3, stars: 0.5}
  pinned: {preset: stormy}
maps: {OUT04.odm: ember, pbp.odm: pinned}
)";

SkyPresetLibrary loadTestLibrary()
{
    SkyPresetLibrary library;
    std::string error;
    const bool loaded = library.loadFromYaml(TestLibraryYaml, error);
    INFO(error);
    REQUIRE(loaded);
    return library;
}
}

TEST_CASE("sky clock parses HH:MM and rejects malformed times")
{
    CHECK(parseClockMinutes("00:00") == 0);
    CHECK(parseClockMinutes("20:45") == 20 * 60 + 45);
    CHECK(parseClockMinutes("23:59") == 23 * 60 + 59);

    for (const char *pText : {"24:00", "12:60", "9:5", "12", "", ":30", "1a:00", "12:3x", "-1:00"})
    {
        CAPTURE(pText);
        CHECK_FALSE(parseClockMinutes(pText));
    }
}

TEST_CASE("sky track interpolates smoothly and wraps across midnight")
{
    const SkyTrack track = {{6 * 60, {0.0f, 0.0f, 0.0f}}, {18 * 60, {1.0f, 2.0f, 4.0f}}};

    CHECK(evaluateSkyTrack(track, 6 * 60)[0] == doctest::Approx(0.0f));
    CHECK(evaluateSkyTrack(track, 18 * 60)[2] == doctest::Approx(4.0f));
    CHECK(evaluateSkyTrack(track, 12 * 60)[1] == doctest::Approx(1.0f));
    // 18:00 -> 06:00 crosses midnight; midnight is halfway back to zero.
    CHECK(evaluateSkyTrack(track, 0.0f)[0] == doctest::Approx(0.5f));
    CHECK(evaluateSkyTrack(track, 24.0f * 60.0f)[0] == doctest::Approx(0.5f));
    CHECK(evaluateSkyTrack(track, 3 * 60)[0] < 0.5f);
    CHECK(evaluateSkyTrack({{720, {0.3f, 0.3f, 0.3f}}}, 100.0f)[0] == doctest::Approx(0.3f));
}

TEST_CASE("sky presets inherit untouched tracks and replace keyed ones")
{
    const SkyPresetLibrary library = loadTestLibrary();
    const SkyPreset *pWet = library.find("wet");
    REQUIRE(pWet);
    CHECK(pWet->tracks[static_cast<size_t>(SkyValue::Zenith)].size() == 1);
    CHECK(pWet->tracks[static_cast<size_t>(SkyValue::Horizon)].size() == 2);
    REQUIRE(pWet->clouds.size() == 2);
    CHECK(pWet->clouds[0].coverage == doctest::Approx(0.9f));
    CHECK_FALSE(pWet->clouds[0].color);
    CHECK(pWet->clouds[1].color);
    CHECK(pWet->clouds[1].texture == "legacy/storm_painting");

    const SkyPreset *pStormy = library.find("stormy");
    REQUIRE(pStormy);
    CHECK(pStormy->storm);
    CHECK(pStormy->moonTexture == "broken_moon");
    CHECK(pStormy->moonPhaseOffset == doctest::Approx(0.5f));
    CHECK(pWet->moonPhaseOffset == doctest::Approx(0.0f));
    CHECK(pWet->moonTexture == "moon");
    CHECK(pStormy->clouds.size() == 2);
    CHECK_FALSE(library.find("deep")->drawSky);
    CHECK(library.presetForSkyName("SKY05") == "day");
    CHECK(library.presetForSkyName("stormclds") == "stormy");
    CHECK(library.presetForSkyName("unknown").empty());
    CHECK(library.presetForWeatherState(0, 7) == "day");
    CHECK(library.presetForWeatherState(3, 7) == "wet");
    CHECK(library.presetForWeatherState(6, 7) == "stormy");
    CHECK(library.presetForWeatherState(-1, 7).empty());
}

TEST_CASE("sky library rejects invalid presets")
{
    const std::string validPreset = "version: 1\nfallback: a\npresets:\n  a:\n    keys:\n      - {time: \"12:00\", "
        "zenith: [0,0,0], horizon: [0,0,0], horizon_exponent: 3, sun_glow: [0,0,0], sun_glow_exponent: 4, "
        "sun_glow_strength: 0, fog: [0,0,0], sun_disc: [0,0,0], sun_disc_visibility: 0, cloud_lit: [0,0,0], "
        "cloud_shadow: [0,0,0], ambient_tint: [1,1,1], water_sun: [1,1,1], water_sky: [0,0,0], stars: 0, "
        "moon_visibility: 0, aerial_haze: 0}\n";
    SkyPresetLibrary library;
    std::string error;
    REQUIRE(library.loadFromYaml(validPreset, error));

    const std::vector<std::string> invalid = {
        "version: 2\nfallback: a\npresets: {a: {}}\n",
        "version: 1\nfallback: a\npresets:\n  a: {keys: [{time: \"12:00\", zenith: [0,0,0]}]}\n",
        validPreset + "  b: {inherits: missing}\n",
        validPreset + "  b: {inherits: b}\n",
        validPreset + "  b: {inherits: a, keys: [{time: \"25:00\", zenith: [0,0,0]}]}\n",
        validPreset + "  b: {inherits: a, keys: [{time: \"12:00\", zenith: [0,0,9]}]}\n",
        validPreset + "  b: {inherits: a, keys: [{time: \"12:00\", zenith: [0,0]}]}\n",
        validPreset + "  b: {inherits: a, keys: [{time: \"12:00\", glitter: 1}]}\n",
        validPreset + "  b: {inherits: a, mystery: 1}\n",
        validPreset + "  b: {inherits: a, below_horizon: lava}\n",
        validPreset + "  b: {inherits: a, clouds: [{coverage: 0.5}]}\n",
        validPreset + "  b: {inherits: a, clouds: [{texture: x, mode: glitter}]}\n",
        validPreset + "  b: {inherits: a, clouds: [{texture: x}, {texture: y}, {texture: z}]}\n",
        validPreset + "aliases: {sky05: missing}\n",
        validPreset + "weather_ladder: [a, missing]\n",
        validPreset + "special: {underwater: missing}\n",
        validPreset + "themes: {t: {sky_tint: [1, 1]}}\n",
        validPreset + "themes: {t: {haze: 2}}\n",
        validPreset + "themes: {t: {glitter: 1}}\n",
        validPreset + "themes: {t: {preset: missing}}\n",
        validPreset + "themes: {t: {}}\nmaps: {out04.odm: missing}\n",
        "version: 1\nfallback: missing\npresets: {}\n",
    };

    for (const std::string &yaml : invalid)
    {
        CAPTURE(yaml);
        CHECK_FALSE(library.loadFromYaml(yaml, error));
        CHECK_FALSE(error.empty());
        CHECK(library.empty());
    }
}

TEST_CASE("sky preset selection follows underwater, debug, environment, weather and precipitation precedence")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyInputs inputs = {};
    CHECK(selectSkyPreset(library, inputs) == "day");

    inputs.weatherSkyName = "stormclds";
    CHECK(selectSkyPreset(library, inputs) == "stormy");

    // The resolved texture name wins; the merged weather ladder only covers names without a preset.
    inputs.mergedWeatherState = 0;
    inputs.mergedWeatherStateCount = 7;
    CHECK(selectSkyPreset(library, inputs) == "stormy");
    inputs.weatherSkyName = "unmapped-sky";
    CHECK(selectSkyPreset(library, inputs) == "day");

    inputs.raining = true;
    CHECK(selectSkyPreset(library, inputs) == "wet");
    inputs.mergedWeatherState = 6;
    CHECK(selectSkyPreset(library, inputs) == "stormy");

    inputs.redFog = true;
    CHECK(selectSkyPreset(library, inputs) == "hot");
    inputs.forcedPreset = "wet";
    CHECK(selectSkyPreset(library, inputs) == "wet");
    inputs.forcedPreset = "not-a-preset";
    CHECK(selectSkyPreset(library, inputs) == "hot");
    inputs.underwater = true;
    CHECK(selectSkyPreset(library, inputs) == "deep");
}

TEST_CASE("sky map themes recolour the selected preset or pin their own")
{
    const SkyPresetLibrary library = loadTestLibrary();
    REQUIRE(library.themeForMap("out04.ODM"));
    CHECK(library.themeForMap("out02.odm") == nullptr);

    SkyInputs inputs = {};
    inputs.gameMinutes = 12.0f * 60.0f;
    inputs.mapFileName = "pbp.odm";
    CHECK(selectSkyPreset(library, inputs) == "stormy");
    inputs.redFog = true;
    CHECK(selectSkyPreset(library, inputs) == "hot");
    inputs.redFog = false;

    SkyStateModel model;
    model.setLibrary(&library);
    inputs.mapFileName = "out02.odm";
    const SkyFrameState plain = model.update(inputs, 0.016f);
    CHECK(plain.themeName.empty());
    CHECK(plain.fogAmount == 0.0f);

    inputs.mapFileName = "out04.odm";
    model.snap();
    const SkyFrameState themed = model.update(inputs, 0.016f);
    CHECK(themed.presetName == "day");
    CHECK(themed.themeName == "ember");
    CHECK(themed.fogAmount == doctest::Approx(0.3f));
    // Grey 0.5 zenith: saturation keeps it grey, the tint warms it, then the haze pulls toward the themed fog.
    CHECK(themed.value(SkyValue::Zenith)[0] > themed.value(SkyValue::Zenith)[2] * 2.0f);
    CHECK(themed.value(SkyValue::Fog)[0] == doctest::Approx(1.0f));
    // White glow stays white under half saturation, then takes the sun tint.
    CHECK(themed.value(SkyValue::SunGlow)[1] == doctest::Approx(0.5f));
    // Stars: theme scale 0.5, then the 0.3 haze dims them like fog.
    CHECK(themed.scalar(SkyValue::Stars) == doctest::Approx(plain.scalar(SkyValue::Stars) * 0.5f * 0.7f));

    // Denser weather fog still wins over the theme's minimum haze; the debug override replaces the map's theme.
    inputs.foggy = true;
    inputs.fogStrongDistance = 2048.0f;
    model.snap();
    CHECK(model.update(inputs, 0.016f).fogAmount > 0.8f);
    inputs.foggy = false;
    inputs.forcedTheme = std::string();
    model.snap();
    CHECK(model.update(inputs, 0.016f).themeName.empty());

    inputs.forcedTheme.reset();
    inputs.underwater = true;
    model.snap();
    CHECK(model.update(inputs, 0.016f).themeName.empty());
}

TEST_CASE("sky state cross-fades weather changes and snaps on clock jumps")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 12.0f * 60.0f;
    const SkyFrameState &day = model.update(inputs, 0.016f);
    CHECK(day.presetName == "day");
    CHECK(day.value(SkyValue::Zenith)[0] == doctest::Approx(0.5f));

    inputs.weatherSkyName = "stormclds";
    model.update(inputs, 0.0f);
    const float halfway = model.update(inputs, 5.0f).value(SkyValue::Zenith)[0];
    CHECK(halfway < 0.5f);
    CHECK(halfway > 0.2f);
    CHECK(model.update(inputs, 6.0f).value(SkyValue::Zenith)[0] == doctest::Approx(0.2f));

    // During the fade both cloud textures are present; afterwards only the target's layers remain.
    inputs.weatherSkyName = "sky05";
    model.update(inputs, 2.0f);
    CHECK(model.frame().clouds.size() == 2);
    model.update(inputs, 20.0f);
    CHECK(model.frame().clouds.size() == 1);

    inputs.weatherSkyName = "stormclds";
    inputs.gameMinutes += 120.0f;
    CHECK(model.update(inputs, 0.016f).value(SkyValue::Zenith)[0] == doctest::Approx(0.2f));

    model.snap();
    inputs.weatherSkyName = "sky05";
    CHECK(model.update(inputs, 0.016f).presetName == "day");
    CHECK(model.frame().moonTexture == "moon");
    inputs.weatherSkyName = "stormclds";
    model.snap();
    CHECK(model.update(inputs, 0.016f).moonTexture == "broken_moon");
}

TEST_CASE("sky state hazes toward fog and keeps authored fog colours")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 18.0f * 60.0f;
    const SkyFrameState clear = model.update(inputs, 0.016f);
    CHECK(clear.fogAmount == 0.0f);
    CHECK(clear.skyMix == 1.0f);

    inputs.foggy = true;
    inputs.fogStrongDistance = 2048.0f;
    model.snap();
    const SkyFrameState foggy = model.update(inputs, 0.016f);
    CHECK(foggy.fogAmount > 0.8f);
    CHECK(foggy.value(SkyValue::Horizon)[0] < clear.value(SkyValue::Horizon)[0]);
    CHECK(foggy.scalar(SkyValue::Stars) < clear.scalar(SkyValue::Stars));

    inputs.authoredFogDisplay = SkyColor{0.9f, 0.7f, 0.5f};
    model.snap();
    const SkyFrameState authored = model.update(inputs, 0.016f);
    CHECK(authored.skyMix == doctest::Approx(0.25f));
    CHECK(authored.fogFlatDisplay[1] == doctest::Approx(0.7f));

    inputs.underwater = true;
    model.snap();
    const SkyFrameState underwater = model.update(inputs, 0.016f);
    CHECK_FALSE(underwater.drawSky);
    CHECK(underwater.skyMix == 0.0f);
}

TEST_CASE("sky state draws an indoor fog cover as one flat colour, and nothing without it")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 23.5f * 60.0f;
    inputs.weatherSkyName = "sky05";
    const SkyFrameState clear = model.update(inputs, 0.016f);

    // A zero cover changes nothing, whatever its colour.
    inputs.fogCoverDisplay = SkyColor{0.5f, 0.5f, 0.5f};
    model.snap();
    const SkyFrameState zero = model.update(inputs, 0.016f);
    CHECK(zero.values == clear.values);
    REQUIRE(zero.clouds.size() == clear.clouds.size());
    for (size_t layer = 0; layer < zero.clouds.size(); ++layer)
    {
        CHECK(zero.clouds[layer].opacity == clear.clouds[layer].opacity);
    }
    CHECK(zero.horizonRing.opacity == clear.horizonRing.opacity);

    // A full cover (MM9's fogged sky box): gradient and clouds in the fog colour, no sun, moon, stars or clouds.
    inputs.fogCover = 1.0f;
    model.snap();
    const SkyFrameState covered = model.update(inputs, 0.016f);
    const float grey = covered.value(SkyValue::Zenith)[0];
    CHECK(grey == doctest::Approx(std::pow(0.5f, 2.2f)).epsilon(0.02));
    for (const SkyValue id : {SkyValue::Zenith, SkyValue::Horizon, SkyValue::CloudLit, SkyValue::CloudShadow})
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            CHECK(covered.value(id)[channel] == doctest::Approx(grey));
        }
    }
    CHECK(covered.scalar(SkyValue::Stars) == 0.0f);
    CHECK(covered.scalar(SkyValue::MoonVisibility) == 0.0f);
    CHECK(covered.scalar(SkyValue::SunDiscVisibility) == 0.0f);
    CHECK(covered.scalar(SkyValue::SunGlowStrength) == 0.0f);
    CHECK(covered.horizonRing.opacity == 0.0f);
    for (const SkyCloudLayerState &layer : covered.clouds)
    {
        CHECK(layer.opacity == 0.0f);
    }
    CHECK(covered.fogFlatDisplay[0] == doctest::Approx(0.5f).epsilon(0.02));
    // The sun's colour and the ambient tint (indoor daylight's hue) are left alone.
    CHECK(covered.value(SkyValue::SunDisc) == clear.value(SkyValue::SunDisc));
    CHECK(covered.value(SkyValue::AmbientTint) == clear.value(SkyValue::AmbientTint));

    // Half way: half the stars.
    inputs.fogCover = 0.5f;
    model.snap();
    const float halfStars = model.update(inputs, 0.016f).scalar(SkyValue::Stars);
    CHECK(halfStars == doctest::Approx(clear.scalar(SkyValue::Stars) * 0.5f));
}

TEST_CASE("sky sun matches the outdoor sun arc and the moon cycles")
{
    // OutdoorWorldRuntime: theta = (minutes - 300) * pi / 960 between 05:00 and 21:00.
    for (const float minutes : {300.0f, 540.0f, 780.0f, 1100.0f, 1260.0f})
    {
        const float angle = (minutes - 300.0f) * 3.14159265f / 960.0f;
        const std::array<float, 3> sun = skySunDirection(minutes);
        CHECK(sun[0] == doctest::Approx(std::cos(angle)));
        CHECK(sun[2] == doctest::Approx(std::sin(angle)));
    }

    CHECK(skySunDirection(23.0f * 60.0f)[2] < 0.0f);
    CHECK(skySunDirection(3.0f * 60.0f)[2] < 0.0f);
    CHECK(skyMoonDirection(0.0f)[2] > 0.3f);
    CHECK(skyMoonDirection(12.0f * 60.0f)[2] < -0.3f);
    CHECK(skyMoonPhase(0.0f) == doctest::Approx(0.0f));
    CHECK(skyMoonPhase(14.0f * 24.0f * 60.0f) == doctest::Approx(0.5f));
    CHECK(skyMoonPhase(28.0f * 24.0f * 60.0f) == doctest::Approx(0.0f));
}

TEST_CASE("sky shows the weather's lightning flash in every preset")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 12.0f * 60.0f;
    CHECK(model.update(inputs, 0.02f).lightningFlash == 0.0f);
    inputs.lightningFlash = 0.8f;
    CHECK(model.update(inputs, 0.02f).lightningFlash == doctest::Approx(0.8f));
    inputs.weatherSkyName = "stormclds";
    model.snap();
    CHECK(model.update(inputs, 0.02f).lightningFlash == doctest::Approx(0.8f));
}

TEST_CASE("sky repository presets load and alias every selectable sky name")
{
    const SkyPresetLibrary library = loadRepositoryLibrary();
    std::vector<std::string> names = {
        // Hardcoded fallbacks and clock swaps in OutdoorWorldRuntime, Dagger Wound, and event overrides.
        "plansky1", "plansky3", "sky01", "sky03", "sky04", "sky05", "sky06", "sky6pm", "sunsetclouds",
        "cloudsabove", "stormclds", "skycity01"};

    std::stringstream continents(readSourceFile("assets_dev/engine/data_tables/continent_settings.txt"));
    std::string line;

    while (std::getline(continents, line))
    {
        const std::vector<std::string> columns = splitTabs(line);

        if (line.empty() || line[0] == '#' || columns.size() < 22)
        {
            continue;
        }

        std::stringstream skies(columns[21]);
        std::string sky;

        while (std::getline(skies, sky, ','))
        {
            if (!trimmed(sky).empty())
            {
                names.push_back(toLowerCopy(trimmed(sky)));
            }
        }
    }

    std::stringstream bolster(readSourceFile("assets_dev/engine/data_tables/bolster_maps.txt"));

    while (std::getline(bolster, line))
    {
        const std::vector<std::string> columns = splitTabs(line);

        if (!line.empty() && line[0] != '#' && columns.size() > 9 && !trimmed(columns[9]).empty())
        {
            names.push_back(toLowerCopy(trimmed(columns[9])));
        }
    }

    CHECK(names.size() > 40);

    for (const std::string &name : names)
    {
        CAPTURE(name);
        CHECK_FALSE(library.presetForSkyName(name).empty());
    }

    for (const char *pSpecial : {"underwater", "plane_fire", "plane_air", "always_dark", "rain", "winter_overcast"})
    {
        CAPTURE(pSpecial);
        CHECK(library.find(pSpecial));
    }

    CHECK(library.presetForWeatherState(0, 7) == "clear");
    CHECK(library.presetForWeatherState(6, 7) == "storm");

    // Every data-selectable original sky keeps its own derived preset with its painting as a colour layer.
    for (const std::string &name : names)
    {
        CAPTURE(name);
        const std::string presetName = library.presetForSkyName(name);
        if (name == "sky6pm")
        {
            continue; // The original night swap is covered by the shared night ramp.
        }
        CHECK(presetName == "legacy_" + name);
        const SkyPreset *pPreset = library.find(presetName);
        REQUIRE(pPreset);
        REQUIRE_FALSE(pPreset->clouds.empty());
        CHECK(pPreset->clouds.front().color);
        CHECK(std::filesystem::exists(std::filesystem::path(OPENYAMM_SOURCE_DIR)
            / ("assets_dev/engine/rendering/sky/" + pPreset->clouds.front().texture + ".oytex")));
    }

    // Dagger Wound's volcanic sky stays red at noon.
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 12.0f * 60.0f;
    inputs.weatherSkyName = "sunsetclouds";
    const SkyFrameState &dagger = model.update(inputs, 0.016f);
    CHECK(dagger.presetName == "legacy_sunsetclouds");
    CHECK(dagger.value(SkyValue::Horizon)[0] > dagger.value(SkyValue::Horizon)[2] * 1.5f);
}

TEST_CASE("a world adds its own skies to the library and redefines none")
{
    const std::string engineText = readSourceFile("assets_dev/engine/rendering/sky/sky.yml");
    const std::string worldText =
        "version: 1\n"
        "aliases: {worldsky1: world_day}\n"
        "presets:\n"
        "  world_day: {inherits: base}\n"
        "maps: {world_x1.odm: scorched}\n";
    std::string composed;
    std::string error;
    REQUIRE(composeSkyLibraryYaml(engineText, {{"world", worldText}}, composed, error));
    SkyPresetLibrary library;
    REQUIRE(library.loadFromYaml(composed, error));
    CHECK(library.presetForSkyName("WorldSky1") == "world_day");
    CHECK(library.find("world_day") != nullptr);
    REQUIRE(library.themeForMap("World_X1.odm") != nullptr);

    CHECK_FALSE(composeSkyLibraryYaml(
        engineText, {{"world", "version: 1\npresets:\n  base: {inherits: base}\n"}}, composed, error));
    CHECK(error.find("defined already") != std::string::npos);
    CHECK_FALSE(composeSkyLibraryYaml(engineText, {{"world", "version: 1\nfallback: base\n"}}, composed, error));

    const std::string xeenText = readSourceFile("assets_dev/worlds/xeen/rendering/sky/sky.yml");
    if (!xeenText.empty())
    {
        REQUIRE(composeSkyLibraryYaml(engineText, {{"xeen", xeenText}}, composed, error));
        CHECK(library.loadFromYaml(composed, error));
        CHECK(library.presetForSkyName("xeendark1") == "xeen_darkside_day");
    }
}

TEST_CASE("sky repository themes name real outdoor maps")
{
    const SkyPresetLibrary library = loadRepositoryLibrary();
    std::stringstream mapStats(readSourceFile("assets_dev/engine/data_tables/map_stats.txt"));
    std::vector<std::string> outdoorMaps;
    std::string line;

    while (std::getline(mapStats, line))
    {
        const std::vector<std::string> columns = splitTabs(line);

        if (columns.size() > 2 && toLowerCopy(trimmed(columns[2])).ends_with(".odm"))
        {
            outdoorMaps.push_back(toLowerCopy(trimmed(columns[2])));
        }
    }

    // The user-named anchors: Ironsand is a hot red desert, Shadowspire a dead necromancer land.
    for (const char *pMap : {"out01.odm", "out04.odm", "out06.odm", "7out05.odm", "7out06.odm", "out09.odm"})
    {
        CAPTURE(pMap);
        CHECK(library.themeForMap(pMap));
    }

    const std::string yaml = readSourceFile("assets_dev/engine/rendering/sky/sky.yml");
    const size_t mapsBegin = yaml.find("\nmaps:\n");
    REQUIRE(mapsBegin != std::string::npos);
    std::stringstream maps(yaml.substr(mapsBegin + 7));

    while (std::getline(maps, line) && (line.empty() || line[0] == ' '))
    {
        const std::string entry = trimmed(line);

        if (entry.empty() || entry[0] == '#')
        {
            continue;
        }

        const std::string mapName = entry.substr(0, entry.find(':'));
        CAPTURE(mapName);
        CHECK(std::find(outdoorMaps.begin(), outdoorMaps.end(), mapName) != outdoorMaps.end());
    }

    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 12.0f * 60.0f;
    inputs.weatherSkyName = "plansky3";
    inputs.mapFileName = "out04.odm";
    const SkyFrameState &ironsand = model.update(inputs, 0.016f);
    CHECK(ironsand.value(SkyValue::Horizon)[0] > ironsand.value(SkyValue::Horizon)[2] * 1.5f);
    CHECK(ironsand.value(SkyValue::Fog)[0] > ironsand.value(SkyValue::Fog)[2] * 1.5f);
}

TEST_CASE("sky night clouds follow the moon")
{
    const SkyPresetLibrary library = loadRepositoryLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.weatherSkyName = "6plansky1";
    const auto cloudLight = [&](float gameMinutes)
    {
        inputs.gameMinutes = gameMinutes;
        model.snap();
        return model.update(inputs, 0.016f).value(SkyValue::CloudLit)[1];
    };

    // Day 0 is a new moon, day 14 a full moon; both at 01:00 with the moon well above the horizon.
    const float newMoon = cloudLight(60.0f);
    const float fullMoon = cloudLight(14.0f * 24.0f * 60.0f + 60.0f);
    CHECK(newMoon < fullMoon * 0.5f);
    CHECK(newMoon > 0.0f);
    // Daylight clouds are untouched by the moon.
    CHECK(cloudLight(12.0f * 60.0f) == doctest::Approx(cloudLight(14.0f * 24.0f * 60.0f + 12.0f * 60.0f)));
}

TEST_CASE("sky repository presets read as day, sunset and night")
{
    const SkyPresetLibrary library = loadRepositoryLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    const auto luminance = [](const SkyColor &color)
    {
        return 0.2126f * color[0] + 0.7152f * color[1] + 0.0722f * color[2];
    };

    inputs.gameMinutes = 13.0f * 60.0f;
    const SkyFrameState noon = model.update(inputs, 0.016f);
    inputs.gameMinutes = 20.0f * 60.0f + 35.0f;
    const SkyFrameState sunset = model.update(inputs, 0.016f);
    inputs.gameMinutes = 23.5f * 60.0f;
    const SkyFrameState night = model.update(inputs, 0.016f);

    // Noon zenith is blue, sunset horizon is warm, night is far darker and starry.
    CHECK(noon.value(SkyValue::Zenith)[2] > noon.value(SkyValue::Zenith)[0] * 2.0f);
    CHECK(sunset.value(SkyValue::Horizon)[0] > sunset.value(SkyValue::Horizon)[2] * 2.0f);
    CHECK(luminance(night.value(SkyValue::Horizon)) < luminance(noon.value(SkyValue::Horizon)) * 0.1f);
    CHECK(night.scalar(SkyValue::Stars) > 0.9f);
    CHECK(noon.scalar(SkyValue::Stars) == 0.0f);
    CHECK(sunset.sunDirection[2] > 0.0f);
    CHECK(sunset.sunDirection[0] < 0.0f);
}

TEST_CASE("distant sea follows the water share of each map side")
{
    constexpr int CellsWide = OutdoorMapData::TerrainWidth - 1;
    constexpr int CellsHigh = OutdoorMapData::TerrainHeight - 1;
    OutdoorMapData map = {};
    map.heightMap.assign(size_t(OutdoorMapData::TerrainWidth) * OutdoorMapData::TerrainHeight, 2);
    map.tileMap.assign(map.heightMap.size(), 0);
    // Land everywhere except the southern rows (grid y grows south) and a scattered western coast.
    std::vector<uint8_t> landMask(size_t(CellsWide) * CellsHigh, 1);

    for (int y = 0; y < CellsHigh; ++y)
    {
        for (int x = 0; x < CellsWide; ++x)
        {
            const bool southSea = y >= CellsHigh - 10;
            const bool westCoast = x < 3 && y % 4 == 0;
            landMask[size_t(y) * CellsWide + size_t(x)] = southSea || westCoast ? 0 : 1;
        }
    }

    const OutdoorDistantSea sea = measureOutdoorDistantSea(map, landMask, nullptr);
    CHECK(sea.sideWeights[2] == doctest::Approx(1.0f)); // south
    CHECK(sea.sideWeights[3] == 0.0f); // north
    CHECK(sea.sideWeights[1] == 0.0f); // east: only its southern corner is water
    CHECK(sea.sideWeights[0] == 0.0f); // west: a quarter-water coast is not open sea
    CHECK(sea.seaLevel == doctest::Approx(2.0f * OutdoorMapData::TerrainHeightScale));
    CHECK(sea.waterColorDisplay[2] > sea.waterColorDisplay[0]);

    map.noTerrain = true;
    CHECK(measureOutdoorDistantSea(map, landMask, nullptr).sideWeights[2] == 0.0f);
}

namespace
{
// The test library with one more preset (indented as a `presets` entry).
std::string withPreset(const std::string &preset)
{
    std::string yaml = TestLibraryYaml;
    const std::string marker = "presets:\n";
    yaml.insert(yaml.find(marker) + marker.size(), preset);
    return yaml;
}
}

TEST_CASE("sky orbit ring is off unless a preset asks for it")
{
    const SkyPresetLibrary repository = loadRepositoryLibrary();

    for (const std::string &name : repository.skyNames())
    {
        const SkyPreset *pPreset = repository.find(repository.presetForSkyName(name));
        REQUIRE(pPreset);
        CAPTURE(name);
        CHECK(pPreset->orbitRing.opacity == 0.0f);
        CHECK(pPreset->orbitRing.lightCount == 0);
    }

    const std::string ringed = withPreset(R"(  ringed:
    inherits: day
    orbit_ring: {opacity: 0.6, width_deg: 5, color: [0.9, 0.8, 1], fragments: 2,
                 lights: {count: 3, size_deg: 0.1, orbit_minutes: [10, 30], color: [1, 0.8, 0.5], brightness: 3}}
)");
    SkyPresetLibrary library;
    std::string error;
    INFO(error);
    REQUIRE(library.loadFromYaml(ringed, error));
    const SkyOrbitRing &ring = library.find("ringed")->orbitRing;
    CHECK(ring.opacity == doctest::Approx(0.6f));
    CHECK(ring.widthDegrees == doctest::Approx(5.0f));
    CHECK(ring.fragments == doctest::Approx(2.0f));
    CHECK(ring.lightCount == 3);
    CHECK(ring.lightSizeDegrees == doctest::Approx(0.1f));
    CHECK(ring.lightOrbitMinutes[0] == doctest::Approx(10.0f));
    CHECK(ring.lightOrbitMinutes[1] == doctest::Approx(30.0f));
    CHECK(ring.lightBrightness == doctest::Approx(3.0f));
    CHECK(library.find("day")->orbitRing.opacity == 0.0f);


    for (const std::string &bad : {"{glitter: 1}", "{opacity: -1}", "{lights: {count: 9}}",
             "{lights: {orbit_minutes: [30, 10]}}", "{lights: {orbit_minutes: [10]}}", "{lights: {spin: 1}}"})
    {
        CAPTURE(bad);
        CHECK_FALSE(library.loadFromYaml(
            withPreset("  bad:\n    inherits: day\n    orbit_ring: " + std::string(bad) + "\n"), error));
    }
}

TEST_CASE("sky orbit lights cross the sky at their own pace and fade with the stars")
{
    SkyOrbitRing ring;
    ring.lightCount = 4;
    ring.lightOrbitMinutes = {20.0f, 45.0f};

    for (int light = 0; light < ring.lightCount; ++light)
    {
        const float start = skyOrbitLightAngle(ring, light, 600.0);
        const float later = skyOrbitLightAngle(ring, light, 601.0);
        CHECK(start >= 0.0f);
        CHECK(start < 6.2832f);
        // At most a twentieth of a turn per game minute; never standing still.
        const float step = std::fabs(later - start);
        CHECK(std::min(step, 6.2832f - step) > 0.1f);
        CHECK(std::min(step, 6.2832f - step) < 0.32f);
        CHECK(skyOrbitLightAngle(ring, light, 600.0) == start);
    }

    CHECK(skyOrbitLightAngle(ring, 0, 600.0) != doctest::Approx(skyOrbitLightAngle(ring, 1, 600.0)));

    const std::string ringed = withPreset(R"(  ringed:
    inherits: day
    orbit_ring: {opacity: 0.5, lights: {count: 2, brightness: 2}}
)");
    SkyPresetLibrary library;
    std::string error;
    REQUIRE(library.loadFromYaml(ringed, error));
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.forcedPreset = "ringed";
    // The test preset's stars rise from 0 at 06:00 to 1 at 18:00.
    inputs.gameMinutes = 6.0f * 60.0f;
    model.snap();
    CHECK(model.update(inputs, 0.02f).orbitRing.opacity == doctest::Approx(0.0f));
    inputs.gameMinutes = 18.0f * 60.0f;
    model.snap();
    const SkyFrameState &night = model.update(inputs, 0.02f);
    CHECK(night.orbitRing.opacity == doctest::Approx(0.5f));
    CHECK(night.orbitRing.lightBrightness == doctest::Approx(2.0f));
    CHECK(night.orbitLightAngles[0] == doctest::Approx(skyOrbitLightAngle(night.orbitRing, 0, 18.0 * 60.0)));
}

TEST_CASE("sky theme rim glow blends day to night by the star weight and fades in haze")
{
    // The test library with more themes (its maps line comes last).
    const auto withThemes = [](const std::string &themes)
    {
        std::string text = TestLibraryYaml;
        text.insert(text.find("maps: {OUT04"), themes);
        return text;
    };
    const std::string text = withThemes(
        "  rim: {rim_glow: {direction_deg: 90, width_deg: 80, height_deg: 10, color: [1, 0.9, 0.7], day: 0.2,"
        " night: 1.0}}\n"
        "  rimhazy: {haze: 0.5, rim_glow: {day: 0.2, night: 1.0}}\n");
    SkyPresetLibrary library;
    std::string error;
    REQUIRE_MESSAGE(library.loadFromYaml(text, error), error);
    const SkyTheme *pTheme = library.findTheme("rim");
    REQUIRE(pTheme != nullptr);
    REQUIRE(pTheme->rimGlow.has_value());
    CHECK(pTheme->rimGlow->widthDegrees == doctest::Approx(80.0f));
    CHECK(pTheme->rimGlow->belowDegrees == doctest::Approx(2.0f));

    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.mapFileName = "out02.odm";
    inputs.gameMinutes = 6.0f * 60.0f;
    CHECK(model.update(inputs, 0.016f).rimGlowStrength == 0.0f);
    CHECK(packSkyRimUniform(model.frame())[1][0] == 0.0f);

    // Stars 0 at 06:00 (day), 1 at 18:00 (night): the strength follows them.
    inputs.forcedTheme = std::string("rim");
    model.snap();
    CHECK(model.update(inputs, 0.016f).rimGlowStrength == doctest::Approx(0.2f));
    inputs.gameMinutes = 18.0f * 60.0f;
    model.snap();
    const SkyFrameState &night = model.update(inputs, 0.016f);
    CHECK(night.rimGlowStrength == doctest::Approx(1.0f));
    const SkyRimUniformValues rim = packSkyRimUniform(night);
    // East: +X; half the width; colour times strength.
    CHECK(rim[0][0] == doctest::Approx(1.0f));
    CHECK(rim[0][1] == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(rim[0][2] == doctest::Approx(40.0f * 3.14159265f / 180.0f));
    CHECK(rim[1][1] == doctest::Approx(0.9f));

    // The theme's haze dims it as it dims the sun's glow.
    inputs.forcedTheme = std::string("rimhazy");
    model.snap();
    CHECK(model.update(inputs, 0.016f).rimGlowStrength == doctest::Approx(1.0f * (1.0f - 0.5f * 0.85f)));

    // Unknown keys are refused.
    SkyPresetLibrary refused;
    CHECK_FALSE(refused.loadFromYaml(withThemes("  bad: {rim_glow: {glow: 1}}\n"), error));
}

TEST_CASE("the void (terrain.void) has no sea past it and counts its own share of each side")
{
    constexpr int CellsWide = OutdoorMapData::TerrainWidth - 1;
    constexpr int CellsHigh = OutdoorMapData::TerrainHeight - 1;
    OutdoorMapData map = {};
    map.heightMap.assign(size_t(OutdoorMapData::TerrainWidth) * OutdoorMapData::TerrainHeight, 0);
    map.tileMap.assign(map.heightMap.size(), 0);
    // Sea along the south (grid y grows south); the east band is void (dry, height 0); land elsewhere.
    std::vector<uint8_t> landMask(size_t(CellsWide) * CellsHigh, 1);
    map.voidCells.assign(map.heightMap.size(), 0);

    for (int y = 0; y < CellsHigh; ++y)
    {
        for (int x = 0; x < CellsWide; ++x)
        {
            landMask[size_t(y) * CellsWide + size_t(x)] = y >= CellsHigh - 10 && x < 100 ? 0 : 1;
            map.voidCells[size_t(y) * OutdoorMapData::TerrainWidth + size_t(x)] = x >= 105 ? 1 : 0;
        }
    }

    const OutdoorDistantSea sea = measureOutdoorDistantSea(map, landMask, nullptr);
    CHECK(sea.voidWeights[1] == doctest::Approx(1.0f)); // east: all void
    CHECK(sea.sideWeights[1] == 0.0f);
    CHECK(sea.sideWeights[2] == doctest::Approx(1.0f)); // south: the void corner counts neither way
    CHECK(sea.voidWeights[2] == 0.0f);
    CHECK(sea.voidWeights[0] == 0.0f);
    CHECK(sea.voidWeights[3] == 0.0f);
    CHECK(isOutdoorVoidCell(map, 110, 5));
    CHECK_FALSE(isOutdoorVoidCell(map, 20, 5));
    CHECK_FALSE(isOutdoorVoidCell(map, -1, 5));

    // Without void cells nothing changes: no void weights, the same sea.
    map.voidCells.clear();
    const OutdoorDistantSea plain = measureOutdoorDistantSea(map, landMask, nullptr);
    CHECK(plain.voidWeights == std::array<float, 4>{});
    CHECK_FALSE(isOutdoorVoidCell(map, 110, 5));
}

TEST_CASE("terrain.void rectangles parse into the map's void cells, and bad ones stop the load")
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04.scene.yml");
    REQUIRE(file.good());
    std::ostringstream stream;
    stream << file.rdbuf();
    const std::string text = stream.str();
    const auto withVoid = [&text](const std::string &rects)
    {
        std::string changed = text;
        const std::string marker = "terrain:\n";
        changed.insert(changed.find(marker) + marker.size(), "  void: " + rects + "\n");
        return changed;
    };
    const OutdoorSceneYmlLoader loader = {};
    std::string error;

    const std::optional<OutdoorSceneData> plain = loader.loadFromText(text, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK(plain->terrainVoidRects.empty());

    const std::optional<OutdoorSceneData> scene = loader.loadFromText(withVoid("[[105, 0, 126, 126], [0, 0, 3, 2]]"),
        error);
    REQUIRE_MESSAGE(scene.has_value(), error);
    REQUIRE(scene->terrainVoidRects.size() == 2);
    CHECK(scene->terrainVoidRects[0] == std::array<int, 4>{105, 0, 126, 126});

    CHECK_FALSE(loader.loadFromText(withVoid("[[5, 0, 4, 3]]"), error).has_value());
    CHECK_FALSE(loader.loadFromText(withVoid("[[0, 0, 128, 3]]"), error).has_value());
    CHECK_FALSE(loader.loadFromText(withVoid("[[0, 0, 3]]"), error).has_value());
    CHECK_FALSE(loader.loadFromText(withVoid("{x: 1}"), error).has_value());

    std::ifstream geometryFile(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04.odm",
        std::ios::binary);
    REQUIRE(geometryFile.good());
    const std::vector<uint8_t> geometryBytes(
        (std::istreambuf_iterator<char>(geometryFile)), std::istreambuf_iterator<char>());
    std::optional<OutdoorMapData> map = OutdoorMapDataLoader{}.loadFromBytes(geometryBytes);
    REQUIRE(map);
    MapDeltaData state;
    REQUIRE_MESSAGE(buildOutdoorMapStateFromScene(*scene, *map, state, error), error);
    REQUIRE(map->voidCells.size() == size_t(OutdoorMapData::TerrainWidth) * OutdoorMapData::TerrainHeight);
    CHECK(isOutdoorVoidCell(*map, 105, 0));
    CHECK(isOutdoorVoidCell(*map, 126, 126));
    CHECK(isOutdoorVoidCell(*map, 3, 2));
    CHECK_FALSE(isOutdoorVoidCell(*map, 104, 50));
    CHECK_FALSE(isOutdoorVoidCell(*map, 4, 2));

    std::optional<OutdoorMapData> plainMap = OutdoorMapDataLoader{}.loadFromBytes(geometryBytes);
    REQUIRE(plainMap);
    MapDeltaData plainState;
    REQUIRE_MESSAGE(buildOutdoorMapStateFromScene(*plain, *plainMap, plainState, error), error);
    CHECK(plainMap->voidCells.empty());
}

TEST_CASE("a sky preset's and a theme's void block set the space below the horizon over the void")
{
    const std::string text = withPreset(R"(  spacey:
    inherits: day
    void: {color: [0.01, 0.02, 0.03], stars: 1.5, limb_deg: 4}
)");
    SkyPresetLibrary library;
    std::string error;
    REQUIRE_MESSAGE(library.loadFromYaml(text, error), error);
    const SkyPreset *pPreset = library.find("spacey");
    REQUIRE(pPreset != nullptr);
    REQUIRE(pPreset->voidLook.has_value());
    CHECK(pPreset->voidLook->stars == doctest::Approx(1.5f));
    CHECK(pPreset->voidLook->limbDegrees == doctest::Approx(4.0f));
    CHECK(pPreset->voidLook->color[2] == doctest::Approx(0.03f));
    CHECK_FALSE(library.find("day")->voidLook.has_value());

    std::string themed = TestLibraryYaml;
    themed.insert(themed.find("maps: {OUT04"), "  dark: {void: {stars: 0.5}}\n");
    SkyPresetLibrary themedLibrary;
    REQUIRE_MESSAGE(themedLibrary.loadFromYaml(themed, error), error);
    SkyStateModel model;
    model.setLibrary(&themedLibrary);
    SkyInputs inputs = {};
    inputs.mapFileName = "out02.odm";
    inputs.gameMinutes = 12.0f * 60.0f;
    // The defaults without a block; the theme's block over them.
    CHECK(model.update(inputs, 0.016f).voidLook.stars == doctest::Approx(SkyVoidLook{}.stars));
    inputs.forcedTheme = std::string("dark");
    model.snap();
    const SkyFrameState &frame = model.update(inputs, 0.016f);
    CHECK(frame.voidLook.stars == doctest::Approx(0.5f));
    CHECK(frame.voidLook.limbDegrees == doctest::Approx(SkyVoidLook{}.limbDegrees));

    SkyPresetLibrary refused;
    CHECK_FALSE(refused.loadFromYaml(withPreset("  bad:\n    inherits: day\n    void: {glow: 1}\n"), error));
}

TEST_CASE("no weather greys the void or hides its stars; fogged geometry still fades into the fog")
{
    const SkyPresetLibrary library = loadTestLibrary();
    SkyStateModel model;
    model.setLibrary(&library);
    SkyInputs inputs = {};
    inputs.gameMinutes = 13.0f * 60.0f;
    const SkyFrameState clear = model.update(inputs, 0.016f);
    CHECK(clear.voidVisibility == 1.0f);
    CHECK(clear.voidFogVisibility == 1.0f);

    // Dense fog weather, then heavy rain in it: the void and its stars stay; geometry fades into the fog colour.
    inputs.foggy = true;
    inputs.fogStrongDistance = 2048.0f;
    model.snap();
    SkyFrameState foggy = model.update(inputs, 0.016f);
    CHECK(foggy.fogAmount > 0.8f);
    CHECK(foggy.voidVisibility == 1.0f);
    CHECK(foggy.voidLook.stars == doctest::Approx(clear.voidLook.stars));
    CHECK(foggy.voidFogVisibility < 0.5f);
    inputs.raining = true;
    inputs.precipitation = 1.0f;
    model.snap();
    foggy = model.update(inputs, 0.016f);
    CHECK(foggy.voidVisibility == 1.0f);
    CHECK(foggy.voidLook.stars == doctest::Approx(clear.voidLook.stars));

    // Only an open sky's fog cover takes the void away.
    inputs.fogCover = 1.0f;
    model.snap();
    CHECK(model.update(inputs, 0.016f).voidVisibility == 0.0f);
}
