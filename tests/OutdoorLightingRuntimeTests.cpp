#include "doctest/doctest.h"

#include "game/outdoor/OutdoorLightingRuntime.h"
#include "game/render/lighting/RenderLight.h"

#include <array>
#include <cstdint>
#include <vector>

using OpenYAMM::Game::OutdoorLightSelectionBounds;
using OpenYAMM::Game::OutdoorLightingRuntime;
using OpenYAMM::Game::OutdoorSelectedFxLights;
using OpenYAMM::Game::RenderLightKind;
using OpenYAMM::Game::WorldFxLightEmitter;

namespace
{
uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

WorldFxLightEmitter makeLight(float x, float y, float z, float radius, uint32_t colorAbgr)
{
    WorldFxLightEmitter light = {};
    light.x = x;
    light.y = y;
    light.z = z;
    light.radius = radius;
    light.colorAbgr = colorAbgr;
    light.kind = RenderLightKind::Projectile;
    return light;
}
}

TEST_CASE("outdoor lighting runtime selects local lights for draw bounds")
{
    std::vector<WorldFxLightEmitter> lights;
    lights.push_back(makeLight(32.0f, 0.0f, 0.0f, 256.0f, makeAbgr(255, 32, 16)));
    lights.push_back(makeLight(5000.0f, 0.0f, 0.0f, 256.0f, makeAbgr(16, 32, 255)));

    OutdoorLightingRuntime runtime;
    runtime.build(lights);

    OutdoorLightSelectionBounds bounds = {};
    bounds.min = {-64.0f, -64.0f, -64.0f};
    bounds.max = {64.0f, 64.0f, 64.0f};
    bounds.valid = true;

    const OutdoorSelectedFxLights selected = runtime.selectForBounds({0.0f, 0.0f, 0.0f}, bounds);

    REQUIRE_EQ(selected.lightCount, 1u);
    CHECK(selected.colors[0] > 0.95f);
    CHECK(selected.colors[2] < 0.10f);
}

TEST_CASE("outdoor lighting runtime point sampling falls off with distance")
{
    std::vector<WorldFxLightEmitter> lights;
    lights.push_back(makeLight(0.0f, 0.0f, 0.0f, 256.0f, makeAbgr(255, 255, 255)));

    OutdoorLightingRuntime runtime;
    runtime.build(lights);

    const std::array<float, 3> nearSample = runtime.sampleLightingRgb({0.0f, 0.0f, 0.0f});
    const std::array<float, 3> farSample = runtime.sampleLightingRgb({1000.0f, 0.0f, 0.0f});

    CHECK(nearSample[0] > 0.5f);
    CHECK(farSample[0] == doctest::Approx(0.0f));
}

TEST_CASE("outdoor lighting runtime clusters dense sectorless projectile lights")
{
    std::vector<WorldFxLightEmitter> lights;

    for (uint32_t index = 0; index < 20; ++index)
    {
        lights.push_back(makeLight(static_cast<float>(index * 10), 32.0f, 64.0f, 128.0f, makeAbgr(255, 64, 32)));
    }

    OutdoorLightingRuntime runtime;
    runtime.build(lights);

    OutdoorLightSelectionBounds bounds = {};
    bounds.min = {-64.0f, -64.0f, 0.0f};
    bounds.max = {320.0f, 128.0f, 128.0f};
    bounds.valid = true;

    const OutdoorSelectedFxLights selected = runtime.selectForBounds({0.0f, 0.0f, 0.0f}, bounds);

    CHECK_EQ(runtime.sourceLightCount(), 20u);
    CHECK_EQ(runtime.outputClusterLightCount(), 1u);
    CHECK_EQ(selected.lightCount, 1u);
}

TEST_CASE("outdoor lighting runtime keeps spread sectorless projectile clusters represented")
{
    std::vector<WorldFxLightEmitter> lights;

    for (uint32_t index = 0; index < 80; ++index)
    {
        const float x = static_cast<float>((index % 16) * 320);
        const float y = static_cast<float>((index / 16) * 320);
        lights.push_back(makeLight(x, y, 128.0f, 128.0f, makeAbgr(255, 64, 32)));
    }

    OutdoorLightingRuntime runtime;
    runtime.build(lights);

    CHECK_EQ(runtime.sourceLightCount(), 80u);
    CHECK(runtime.outputClusterLightCount() <= OutdoorSelectedFxLights::MaxLights);

    const std::array<float, 3> leftSample = runtime.sampleLightingRgb({0.0f, 0.0f, 128.0f});
    const std::array<float, 3> rightSample = runtime.sampleLightingRgb({4800.0f, 1280.0f, 128.0f});
    const std::array<float, 3> farSample = runtime.sampleLightingRgb({9000.0f, 4500.0f, 128.0f});
    CHECK(leftSample[0] > 0.0f);
    CHECK(rightSample[0] > 0.0f);
    CHECK(farSample[0] == doctest::Approx(0.0f));
}
