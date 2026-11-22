#include "doctest/doctest.h"

#include "game/audio/WorldAmbientSounds.h"
#include "game/events/EventRuntime.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <optional>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("world ambient sounds are heard within reach and their time of day")
{
    WorldAmbientSound waves = {};
    waves.sound = "ambient/water/waves02.wav";
    waves.position = {1000.0f, 0.0f, 0.0f};
    waves.innerRadius = 256.0f;
    waves.outerRadius = 1024.0f;
    const float noon = 12.0f * 60.0f;
    const float midnight = 24.0f * 60.0f * 3.0f;

    CHECK(worldAmbientSoundAudible(waves, {0.0f, 0.0f, 0.0f}, noon, false));
    CHECK_FALSE(worldAmbientSoundAudible(waves, {-100.0f, 0.0f, 0.0f}, noon, false));
    // a playing sound keeps going a little past its reach
    CHECK(worldAmbientSoundAudible(waves, {-100.0f, 0.0f, 0.0f}, noon, true));
    CHECK_FALSE(worldAmbientSoundAudible(waves, {-200.0f, 0.0f, 0.0f}, noon, true));

    WorldAmbientSound birds = waves;
    birds.dayOnly = true;
    CHECK(worldAmbientSoundAudible(birds, {1000.0f, 0.0f, 0.0f}, noon, false));
    CHECK_FALSE(worldAmbientSoundAudible(birds, {1000.0f, 0.0f, 0.0f}, midnight, false));

    WorldAmbientSound owls = waves;
    owls.nightOnly = true;
    CHECK_FALSE(worldAmbientSoundAudible(owls, {1000.0f, 0.0f, 0.0f}, noon, false));
    CHECK(worldAmbientSoundAudible(owls, {1000.0f, 0.0f, 0.0f}, midnight + 23.0f * 60.0f, false));

    WorldAmbientSound off = waves;
    off.startOn = false;
    CHECK_FALSE(worldAmbientSoundAudible(off, {1000.0f, 0.0f, 0.0f}, noon, false));
}

TEST_CASE("a map script switches ambient sounds through AmbientSound<key>")
{
    WorldAmbientSound crowd = {};
    crowd.key = 40017;
    crowd.position = {0.0f, 0.0f, 0.0f};
    crowd.outerRadius = 1024.0f;
    crowd.startOn = false;
    const float noon = 12.0f * 60.0f;
    const std::array<float, 3> here = {0.0f, 0.0f, 0.0f};
    std::unordered_map<std::string, int32_t> vars;

    CHECK_FALSE(worldAmbientSoundSwitch(crowd, nullptr).has_value());
    CHECK_FALSE(worldAmbientSoundSwitch(crowd, &vars).has_value());
    CHECK_FALSE(worldAmbientSoundAudible(crowd, here, noon, false, worldAmbientSoundSwitch(crowd, &vars)));

    vars["AmbientSound40017"] = 1;
    CHECK(worldAmbientSoundAudible(crowd, here, noon, false, worldAmbientSoundSwitch(crowd, &vars)));

    vars["AmbientSound40017"] = 2;
    crowd.startOn = true;
    CHECK_FALSE(worldAmbientSoundAudible(crowd, here, noon, false, worldAmbientSoundSwitch(crowd, &vars)));

    vars["AmbientSound40017"] = 0;
    CHECK(worldAmbientSoundAudible(crowd, here, noon, false, worldAmbientSoundSwitch(crowd, &vars)));
}

TEST_CASE("a world's day hours decide its day-only and night-only ambient sounds")
{
    WorldAmbientSound owls = {};
    owls.outerRadius = 1024.0f;
    owls.nightOnly = true;
    const std::array<float, 3> here = {0.0f, 0.0f, 0.0f};
    const WorldAmbientSoundRules mm9 = {5.0f, 17.0f, false};
    const float sixPm = 18.0f * 60.0f;
    const float halfPastFive = 5.5f * 60.0f;

    // MM6-MM8's 06:00-20:00 day; MM9's 05:00-17:00 (MM9_AMBIENT_AUDIO_RE.md "Day and night")
    CHECK_FALSE(worldAmbientSoundAudible(owls, here, sixPm, false));
    CHECK(worldAmbientSoundAudible(owls, here, sixPm, false, std::nullopt, mm9));
    CHECK(worldAmbientSoundAudible(owls, here, halfPastFive, false));
    CHECK_FALSE(worldAmbientSoundAudible(owls, here, halfPastFive, false, std::nullopt, mm9));
    CHECK(worldAmbientSoundDaytime(17.0f * 60.0f - 1.0f, mm9));
    CHECK_FALSE(worldAmbientSoundDaytime(17.0f * 60.0f, mm9));
    CHECK(worldAmbientSoundDaytime(5.0f * 60.0f + 24.0f * 60.0f, mm9));
}

TEST_CASE("a fire's sound follows its decoration's evt.SetSprite")
{
    WorldAmbientSound fire = {};
    fire.key = 582;
    fire.outerRadius = 512.0f;
    fire.startOn = false;
    fire.spriteCog = 310;
    EventRuntimeState events;

    CHECK_FALSE(worldAmbientSoundEventSwitch(fire, &events).has_value());
    events.spriteOverrides[310].hidden = false;
    CHECK(worldAmbientSoundEventSwitch(fire, &events) == std::optional<bool>(true));
    events.spriteOverrides[310].hidden = true;
    CHECK(worldAmbientSoundEventSwitch(fire, &events) == std::optional<bool>(false));
    // the map variable, set by a script, wins
    events.namedMapVars["AmbientSound582"] = 1;
    CHECK(worldAmbientSoundEventSwitch(fire, &events) == std::optional<bool>(true));

    WorldAmbientSound plain = fire;
    plain.spriteCog = 0;
    events.namedMapVars.clear();
    CHECK_FALSE(worldAmbientSoundEventSwitch(plain, &events).has_value());
}

TEST_CASE("indoor scene ambient sounds parse")
{
    const std::string yaml = R"(
- {key: 12, sound: ambient/water/waves02.wav, position: [1, 2, 3], inner_radius: 640, outer_radius: 3072,
   volume: 0.8, wait: [2, 6], day_only: true}
- {key: 13, sound: ambient/fire/torchlight.wav, position: [0, 0, 0], outer_radius: 512, loop: false, start_on: false,
   sprite: 310}
)";
    std::vector<WorldAmbientSound> sounds;
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneAmbientSounds(yaml, sounds, error), error);
    REQUIRE(sounds.size() == 2);
    CHECK(sounds[0].key == 12);
    CHECK(sounds[0].sound == "ambient/water/waves02.wav");
    CHECK(sounds[0].innerRadius == doctest::Approx(640.0f));
    CHECK(sounds[0].volume == doctest::Approx(0.8f));
    CHECK(sounds[0].loop);
    CHECK(sounds[0].waitMinSeconds == doctest::Approx(2.0f));
    CHECK(sounds[0].waitMaxSeconds == doctest::Approx(6.0f));
    CHECK(sounds[0].dayOnly);
    CHECK_FALSE(sounds[1].loop);
    CHECK_FALSE(sounds[1].startOn);
    CHECK(sounds[0].spriteCog == 0);
    CHECK(sounds[1].spriteCog == 310);
    CHECK(sounds[1].volume == doctest::Approx(1.0f));

    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, sound: a.wav, position: [0, 0, 0], inner_radius: 10, "
                                              "outer_radius: 5}", sounds, error));
    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, sound: a.wav, position: [0, 0, 0], outer_radius: 5, "
                                              "wait: [3, 1]}", sounds, error));
    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, position: [0, 0, 0], outer_radius: 5}", sounds, error));
}

TEST_CASE("outdoor scene ambient sounds parse, an overlay's replace the base scene's, and reach the map data (E9)")
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04.scene.yml");
    REQUIRE(file.good());
    std::ostringstream text;
    text << file.rdbuf();
    const OutdoorSceneYmlLoader loader = {};
    std::string error;

    // The shipped scene has none.
    const std::optional<OutdoorSceneData> plain = loader.loadFromText(text.str(), error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK(plain->ambientSounds.empty());

    // A base scene's list.
    std::optional<OutdoorSceneData> scene = loader.loadFromText(text.str()
        + "\nambient_sounds:\n  - {key: 1, sound: ambient/wind.wav, position: [100, 200, 300], inner_radius: 2000, "
          "outer_radius: 9000, volume: 0.5}\n", error);
    REQUIRE_MESSAGE(scene.has_value(), error);
    REQUIRE(scene->ambientSounds.size() == 1);
    CHECK(scene->ambientSounds[0].sound == "ambient/wind.wav");
    CHECK(scene->ambientSounds[0].outerRadius == doctest::Approx(9000.0f));

    // An overlay's list replaces it.
    REQUIRE_MESSAGE(loader.applyOverlayFromText(*scene, "format_version: 1\nkind: \"outdoor_scene_overlay\"\n"
        "source:\n  geometry_file: \"out04.odm\"\nambient_sounds:\n"
        "  - {key: 7, sound: ambient/sandfall.wav, position: [0, 0, 0], outer_radius: 3000, wait: [1, 2]}\n"
        "  - {key: 8, sound: ambient/sandfall.wav, position: [9, 9, 9], outer_radius: 3000, night_only: true}\n", error),
        error);
    REQUIRE(scene->ambientSounds.size() == 2);
    CHECK(scene->ambientSounds[0].key == 7);
    CHECK(scene->ambientSounds[1].nightOnly);

    // A bad entry stops the load with the reason.
    CHECK_FALSE(loader.loadFromText(text.str() + "\nambient_sounds:\n  - {key: 1, position: [0, 0, 0], "
        "outer_radius: 5}\n", error).has_value());

    std::ifstream geometryFile(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04.odm",
        std::ios::binary);
    REQUIRE(geometryFile.good());
    const std::vector<uint8_t> geometryBytes(
        (std::istreambuf_iterator<char>(geometryFile)), std::istreambuf_iterator<char>());
    std::optional<OutdoorMapData> map = OutdoorMapDataLoader{}.loadFromBytes(geometryBytes);
    REQUIRE(map);
    MapDeltaData state;
    REQUIRE_MESSAGE(buildOutdoorMapStateFromScene(*scene, *map, state, error), error);
    CHECK(map->ambientSounds.size() == 2);
}

TEST_CASE("D-48: a placed sound pans only when its world's rules and its own `pan` both say so")
{
    std::vector<WorldAmbientSound> sounds;
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneAmbientSounds("- {key: 1, sound: a.wav, position: [0, 0, 0], outer_radius: 500, "
        "pan: false}\n- {key: 2, sound: a.wav, position: [0, 0, 0], outer_radius: 500}\n", sounds, error), error);
    REQUIRE(sounds.size() == 2);
    CHECK_FALSE(sounds[0].pan);
    CHECK(sounds[1].pan);
    WorldAmbientSoundRules rules;
    CHECK_FALSE(worldAmbientSoundPans(sounds[0], rules));
    CHECK(worldAmbientSoundPans(sounds[1], rules));
    rules.pan = false;
    CHECK_FALSE(worldAmbientSoundPans(sounds[1], rules));
}

TEST_CASE("D-48: a loop without a wait starts anywhere in its clip; one-shots and waiting sounds at its start")
{
    std::mt19937 rng(7u);
    WorldAmbientSound loop;
    loop.loop = true;
    float lowest = 1.0f;
    float highest = 0.0f;

    for (int index = 0; index < 200; ++index)
    {
        const float fraction = worldAmbientSoundStartFraction(loop, rng);
        CHECK(fraction >= 0.0f);
        CHECK(fraction < 1.0f);
        lowest = std::min(lowest, fraction);
        highest = std::max(highest, fraction);
    }

    // Spread over the clip, not all at one place.
    CHECK(lowest < 0.1f);
    CHECK(highest > 0.9f);
    WorldAmbientSound once;
    once.loop = false;
    CHECK(worldAmbientSoundStartFraction(once, rng) == 0.0f);
    WorldAmbientSound waves = loop;
    waves.waitMinSeconds = 2.0f;
    waves.waitMaxSeconds = 6.0f;
    CHECK(worldAmbientSoundStartFraction(waves, rng) == 0.0f);
}
