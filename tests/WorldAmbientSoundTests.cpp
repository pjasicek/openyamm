#include "doctest/doctest.h"

#include "game/audio/WorldAmbientSounds.h"
#include "game/events/EventRuntime.h"
#include "game/maps/IndoorSceneYml.h"

#include <array>
#include <optional>
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
