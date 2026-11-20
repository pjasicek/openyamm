#include "doctest/doctest.h"

#include "game/maps/MistYml.h"
#include "game/fx/MistWisps.h"
#include "game/fx/ParticleSystem.h"
#include "game/render/Mist.h"

using OpenYAMM::Game::MapMist;
using OpenYAMM::Game::MaxMistVolumes;
using OpenYAMM::Game::MistLayer;
using OpenYAMM::Game::MistUniformValues;
using OpenYAMM::Game::MistVolume;
using OpenYAMM::Game::mistLayerCover;
using OpenYAMM::Game::mistVolumeCover;
using OpenYAMM::Game::packMistUniform;
using OpenYAMM::Game::parseSceneMist;
using OpenYAMM::Game::selectMistVolumes;

TEST_CASE("mist: a map without the block packs nothing")
{
    const MapMist mist;
    CHECK_FALSE(mist.enabled());
    for (const std::array<float, 4> &vector : packMistUniform(mist, {0.0f, 0.0f, 0.0f}, 12.0f))
    {
        for (const float value : vector)
        {
            CHECK(value == 0.0f);
        }
    }
}

TEST_CASE("mist: the scene block parses a layer and volumes")
{
    MapMist mist;
    std::string error;
    REQUIRE(parseSceneMist(
        "layer: {color_rgb: [51, 102, 204], base_height: 100, falloff_height: 200, visibility: 4000,\n"
        "        max_opacity: 0.5, noise: 0.25, noise_size: 800, drift: [3, -4], follow_daylight: false}\n"
        "volumes:\n"
        "  - {position: [1, 2, 3], radius: 300, color_rgb: [255, 0, 0], visibility: 250}\n"
        "  - {position: [4, 5, 6], radius: [100, 200, 50], color_rgb: [0, 255, 0], visibility: 500, noise: 0}\n",
        mist, error));
    REQUIRE(mist.layers.size() == 1);
    CHECK(mist.layers[0].depth < 0.0f);
    CHECK(mist.layers[0].color[0] == doctest::Approx(0.2f));
    CHECK(mist.layers[0].color[2] == doctest::Approx(0.8f));
    CHECK(mist.layers[0].baseHeight == 100.0f);
    CHECK(mist.layers[0].falloffHeight == 200.0f);
    CHECK(mist.layers[0].visibility == 4000.0f);
    CHECK(mist.layers[0].maxOpacity == 0.5f);
    CHECK(mist.layers[0].drift[1] == -4.0f);
    CHECK_FALSE(mist.layers[0].followsDaylight);
    REQUIRE(mist.volumes.size() == 2);
    CHECK(mist.volumes[0].radius[2] == 300.0f);
    CHECK(mist.volumes[1].radius[1] == 200.0f);
    CHECK(mist.volumes[1].noise == 0.0f);
    CHECK(mist.volumes[0].followsDaylight);
}

TEST_CASE("mist: the scene block refuses unknown keys and values out of range")
{
    MapMist mist;
    std::string error;
    CHECK_FALSE(parseSceneMist("layer: {color_rgb: [1, 2, 3], base_height: 0, falloff_height: 100}", mist, error));
    CHECK_FALSE(parseSceneMist(
        "layer: {color_rgb: [1, 2, 3], base_height: 0, falloff_height: 100, visibility: 0}", mist, error));
    CHECK_FALSE(parseSceneMist(
        "layer: {color_rgb: [1, 2, 300], base_height: 0, falloff_height: 100, visibility: 10}", mist, error));
    CHECK_FALSE(parseSceneMist(
        "layer: {color_rgb: [1, 2, 3], base_height: 0, falloff_height: 100, visibility: 10, thick: 1}", mist, error));
    CHECK_FALSE(parseSceneMist("volumes: [{position: [0, 0, 0], radius: 0, color_rgb: [1, 2, 3], visibility: 5}]",
        mist, error));
    CHECK_FALSE(parseSceneMist("clouds: {}", mist, error));
    CHECK_FALSE(mist.enabled());
}

TEST_CASE("mist: the layer hides more over a longer way and less from above")
{
    MistLayer layer;
    layer.baseHeight = 0.0f;
    layer.falloffHeight = 100.0f;
    layer.visibility = 1000.0f;
    layer.maxOpacity = 0.9f;

    // Inside the densest mist the cover follows the visibility distance: 63 % at one visibility.
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 0.0f}, {1000.0f, 0.0f, 0.0f}) == doctest::Approx(0.632f).epsilon(0.01));
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 0.0f}, {300.0f, 0.0f, 0.0f})
        < mistLayerCover(layer, {0.0f, 0.0f, 0.0f}, {600.0f, 0.0f, 0.0f}));
    // It never covers more than its most.
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 0.0f}, {100000.0f, 0.0f, 0.0f}) == doctest::Approx(0.9f));
    // The same way high above the base crosses almost none of it.
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 800.0f}, {1000.0f, 0.0f, 800.0f}) < 0.01f);
    // Looking down into it from above hides less than looking along it.
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 500.0f}, {0.0f, 0.0f, 0.0f})
        < mistLayerCover(layer, {0.0f, 0.0f, 0.0f}, {500.0f, 0.0f, 0.0f}));
    // The same both ways.
    CHECK(mistLayerCover(layer, {0.0f, 0.0f, 500.0f}, {700.0f, 0.0f, 20.0f})
        == doctest::Approx(mistLayerCover(layer, {700.0f, 0.0f, 20.0f}, {0.0f, 0.0f, 500.0f})));
}

TEST_CASE("mist: a volume hides only what lies behind or inside it")
{
    MistVolume volume;
    volume.position = {0.0f, 0.0f, 0.0f};
    volume.radius = {100.0f, 100.0f, 50.0f};
    volume.visibility = 100.0f;
    volume.maxOpacity = 1.0f;

    // Through the centre along x: the density 1 - r^2 over the chord of 200 integrates to 4/3 of the radius.
    CHECK(mistVolumeCover(volume, {-500.0f, 0.0f, 0.0f}, {500.0f, 0.0f, 0.0f})
        == doctest::Approx(1.0f - std::exp(-4.0f / 3.0f)).epsilon(0.001));
    // A ray that misses it, one that stops before it and one that starts past it.
    CHECK(mistVolumeCover(volume, {-500.0f, 0.0f, 80.0f}, {500.0f, 0.0f, 80.0f}) == 0.0f);
    CHECK(mistVolumeCover(volume, {-500.0f, 0.0f, 0.0f}, {-200.0f, 0.0f, 0.0f}) == 0.0f);
    CHECK(mistVolumeCover(volume, {200.0f, 0.0f, 0.0f}, {500.0f, 0.0f, 0.0f}) == 0.0f);
    // From the centre outward: half of the full way.
    CHECK(mistVolumeCover(volume, {0.0f, 0.0f, 0.0f}, {500.0f, 0.0f, 0.0f})
        == doctest::Approx(1.0f - std::exp(-2.0f / 3.0f)).epsilon(0.001));
    // Near its edge it is thinner than through its middle.
    CHECK(mistVolumeCover(volume, {-500.0f, 90.0f, 0.0f}, {500.0f, 90.0f, 0.0f})
        < mistVolumeCover(volume, {-500.0f, 30.0f, 0.0f}, {500.0f, 30.0f, 0.0f}));
}

TEST_CASE("mist: the nearest volumes are drawn, and one about to be left out has faded")
{
    std::vector<MistVolume> volumes;
    for (size_t index = 0; index < MaxMistVolumes + 2; ++index)
    {
        MistVolume volume;
        volume.position = {float(index) * 1000.0f, 0.0f, 0.0f};
        volume.radius = {100.0f, 100.0f, 100.0f};
        volumes.push_back(volume);
    }

    const std::vector<std::pair<size_t, float>> selected = selectMistVolumes(volumes, {0.0f, 0.0f, 0.0f});
    REQUIRE(selected.size() == MaxMistVolumes);
    CHECK(selected.front().first == 0);
    CHECK(selected.front().second == 1.0f);
    CHECK(selected.back().first == MaxMistVolumes - 1);
    // The first one left out is 6 000 - 100 away; the last drawn one, 1 000 nearer, has kept most of a quarter's fade.
    CHECK(selected.back().second > 0.0f);
    CHECK(selected.back().second < 1.0f);

    volumes.resize(2);
    const std::vector<std::pair<size_t, float>> few = selectMistVolumes(volumes, {5000.0f, 0.0f, 0.0f});
    REQUIRE(few.size() == 2);
    CHECK(few[0].first == 1);
    CHECK(few[1].second == 1.0f);
}

TEST_CASE("mist: the uniform carries the layer, the daylight and the drift")
{
    MapMist mist;
    mist.layers.emplace_back();
    mist.layers[0].color = {0.5f, 0.6f, 0.7f};
    mist.layers[0].baseHeight = 64.0f;
    mist.layers[0].falloffHeight = 200.0f;
    mist.layers[0].visibility = 1000.0f;
    mist.layers[0].noiseSize = 500.0f;
    mist.layers[0].drift = {10.0f, 0.0f};
    MistVolume volume;
    volume.position = {1.0f, 2.0f, 3.0f};
    volume.radius = {10.0f, 20.0f, 40.0f};
    volume.visibility = 50.0f;
    volume.color = {1.0f, 1.0f, 1.0f};
    volume.followsDaylight = false;
    mist.volumes.push_back(volume);

    const MistUniformValues values = packMistUniform(mist, {0.0f, 0.0f, 0.0f}, 100.0f, {0.5f, 0.5f, 0.5f});
    // Counts, then the volumes' patches (the first layer's).
    CHECK(values[0][0] == 1.0f);
    CHECK(values[0][1] == 1.0f);
    CHECK(values[1][0] == doctest::Approx(1.0f / 500.0f));
    // The layer.
    CHECK(values[2][0] == doctest::Approx(0.25f));
    CHECK(values[2][3] == doctest::Approx(0.9f));
    CHECK(values[3][0] == 64.0f);
    CHECK(values[3][1] == doctest::Approx(1.0f / 200.0f));
    CHECK(values[3][2] == doctest::Approx(1.0f / 1000.0f));
    CHECK(values[4][0] == 0.0f);
    CHECK(values[4][1] == doctest::Approx(1.0f / 500.0f));
    CHECK(values[4][2] == doctest::Approx(2.0f));
    // The volume, after the layers' slots.
    const size_t volume0 = 2 + 3 * OpenYAMM::Game::MaxMistLayers;
    CHECK(values[volume0][3] == doctest::Approx(1.0f / 50.0f));
    CHECK(values[volume0 + 1][2] == doctest::Approx(1.0f / 40.0f));
    // A volume that does not follow the daylight keeps its colour.
    CHECK(values[volume0 + 2][0] == 1.0f);
}

TEST_CASE("mist: several layers, each ending at its depth below its base")
{
    MapMist mist;
    std::string error;
    REQUIRE(parseSceneMist(
        "layers:\n"
        "  - {color_rgb: [10, 20, 30], base_height: -1500, depth: 40, falloff_height: 100, visibility: 500}\n"
        "  - {color_rgb: [40, 50, 60], base_height: -700, depth: 40, falloff_height: 100, visibility: 500}\n",
        mist, error));
    REQUIRE(mist.layers.size() == 2);
    CHECK(mist.layers[1].depth == 40.0f);

    // The upper floor's mist: thick along its own floor, none on the floor far below it.
    const MistLayer &upper = mist.layers[1];
    CHECK(mistLayerCover(upper, {0.0f, 0.0f, -690.0f}, {500.0f, 0.0f, -690.0f}) > 0.5f);
    CHECK(mistLayerCover(upper, {0.0f, 0.0f, -1400.0f}, {500.0f, 0.0f, -1400.0f}) < 0.001f);
    // A view down a shaft crosses little more than the way to just under the floor.
    const float throughShaft = mistLayerCover(upper, {0.0f, 0.0f, -690.0f}, {0.0f, 0.0f, -1500.0f});
    const float toUnderFloor = mistLayerCover(upper, {0.0f, 0.0f, -690.0f}, {0.0f, 0.0f, -900.0f});
    CHECK(throughShaft == doctest::Approx(toUnderFloor).epsilon(0.02));
    // The same both ways across the base.
    CHECK(mistLayerCover(upper, {0.0f, 0.0f, -600.0f}, {300.0f, 0.0f, -760.0f})
        == doctest::Approx(mistLayerCover(upper, {300.0f, 0.0f, -760.0f}, {0.0f, 0.0f, -600.0f})));
    // Without a depth the same layer fills everything below it.
    MistLayer endless = upper;
    endless.depth = -1.0f;
    CHECK(mistLayerCover(endless, {0.0f, 0.0f, -1400.0f}, {500.0f, 0.0f, -1400.0f}) > 0.5f);

    CHECK(packMistUniform(mist, {0.0f, 0.0f, 0.0f}, 0.0f)[0][0] == 2.0f);
    CHECK(packMistUniform(mist, {0.0f, 0.0f, 0.0f}, 0.0f)[2 + 3 + 2][0] == doctest::Approx(1.0f / 40.0f));

    CHECK_FALSE(parseSceneMist(
        "layer: {color_rgb: [1, 2, 3], base_height: 0, falloff_height: 100, visibility: 10}\nlayers: []", mist, error));
    CHECK_FALSE(parseSceneMist(
        "layers: [{color_rgb: [1, 2, 3], base_height: 0, falloff_height: 100, visibility: 10, depth: -5}]", mist,
        error));
}

TEST_CASE("mist wisps: they stand only where the mist is, near the eye, and keep their number")
{
    using OpenYAMM::Game::FxParticleState;
    using OpenYAMM::Game::FxParticleTag;
    using OpenYAMM::Game::MistWisps;
    using OpenYAMM::Game::ParticleSystem;
    using OpenYAMM::Game::sampleMist;

    MapMist mist;
    mist.layers.emplace_back();
    mist.layers[0].baseHeight = 0.0f;
    mist.layers[0].falloffHeight = 100.0f;
    mist.layers[0].color = {0.2f, 0.4f, 0.6f};

    CHECK(sampleMist(mist, {0.0f, 0.0f, -50.0f}).density == doctest::Approx(1.0f));
    CHECK(sampleMist(mist, {0.0f, 0.0f, 100.0f}).density == doctest::Approx(std::exp(-1.0f)));
    CHECK(sampleMist(mist, {0.0f, 0.0f, 100.0f}).color[2] == doctest::Approx(0.6f));
    CHECK(sampleMist(MapMist{}, {0.0f, 0.0f, 0.0f}).density == 0.0f);

    ParticleSystem particles;
    MistWisps wisps;
    const std::array<float, 3> eye = {1000.0f, 2000.0f, 120.0f};
    wisps.update(mist, eye, 0.0f, {1.0f, 1.0f, 1.0f}, particles);
    CHECK(particles.particleCount() > MistWisps::TargetCount / 2);
    CHECK(particles.particleCount() <= MistWisps::TargetCount);
    for (const FxParticleState &particle : particles.particles())
    {
        CHECK(particle.tag == FxParticleTag::MapMist);
        const float dx = particle.x - eye[0];
        const float dy = particle.y - eye[1];
        CHECK(std::sqrt(dx * dx + dy * dy) <= MistWisps::SpawnRadius + 1.0f);
        CHECK(particle.z < eye[2]);
    }

    // More frames never raise the number past the target.
    for (int frame = 1; frame <= 600; ++frame)
    {
        wisps.update(mist, eye, float(frame) / 60.0f, {1.0f, 1.0f, 1.0f}, particles);
        particles.update(1.0f / 60.0f);
        CHECK(particles.particleCount() <= MistWisps::TargetCount);
    }
    CHECK(particles.particleCount() > MistWisps::TargetCount / 2);

    // A teleport leaves the old wisps behind: they go, and new ones stand around the eye.
    const std::array<float, 3> away = {90000.0f, 2000.0f, 120.0f};
    wisps.update(mist, away, 11.0f, {1.0f, 1.0f, 1.0f}, particles);
    wisps.update(mist, away, 11.02f, {1.0f, 1.0f, 1.0f}, particles);
    for (const FxParticleState &particle : particles.particles())
    {
        CHECK(std::abs(particle.x - away[0]) <= MistWisps::SpawnRadius + 1.0f);
    }

    // High above the mist there is none to stand in.
    ParticleSystem empty;
    MistWisps none;
    none.update(MapMist{}, eye, 0.0f, {1.0f, 1.0f, 1.0f}, empty);
    CHECK(empty.particleCount() == 0);
}
