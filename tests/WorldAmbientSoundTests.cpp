#include "doctest/doctest.h"

#include "game/audio/WorldAmbientSounds.h"
#include "game/maps/IndoorSceneYml.h"

#include <string>
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

TEST_CASE("indoor scene ambient sounds parse")
{
    const std::string yaml = R"(
- {key: 12, sound: ambient/water/waves02.wav, position: [1, 2, 3], inner_radius: 640, outer_radius: 3072,
   volume: 0.8, wait: [2, 6], day_only: true}
- {key: 13, sound: ambient/fire/torchlight.wav, position: [0, 0, 0], outer_radius: 512, loop: false, start_on: false}
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
    CHECK(sounds[1].volume == doctest::Approx(1.0f));

    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, sound: a.wav, position: [0, 0, 0], inner_radius: 10, "
                                              "outer_radius: 5}", sounds, error));
    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, sound: a.wav, position: [0, 0, 0], outer_radius: 5, "
                                              "wait: [3, 1]}", sounds, error));
    CHECK_FALSE(parseIndoorSceneAmbientSounds("- {key: 1, position: [0, 0, 0], outer_radius: 5}", sounds, error));
}
