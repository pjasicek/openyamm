#include "doctest/doctest.h"

#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorWater.h"
#include "game/maps/IndoorSceneYml.h"

#include <cmath>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
IndoorWaterPiece box(float x0, float y0, float x1, float y1, float bottom, float top)
{
    IndoorWaterPiece piece;
    piece.polygon = {{x0, y0}, {x1, y0}, {x1, y1}, {x0, y1}};
    piece.bottom = bottom;
    piece.top = top;
    finalizeIndoorWaterPiece(piece);
    return piece;
}

// A pool 1000 square, its surface at 0 and its bed at -400, and an L-shaped second pool of two pieces.
std::vector<IndoorWaterVolume> pools()
{
    std::vector<IndoorWaterVolume> volumes(2);
    volumes[0].id = "Pool";
    volumes[0].pieces.push_back(box(0.0f, 0.0f, 1000.0f, 1000.0f, -400.0f, 0.0f));
    volumes[1].id = "Ell";
    volumes[1].pieces.push_back(box(2000.0f, 0.0f, 2200.0f, 1000.0f, -300.0f, -50.0f));
    volumes[1].pieces.push_back(box(2200.0f, 800.0f, 3000.0f, 1000.0f, -200.0f, -50.0f));
    return volumes;
}

bool near(float a, float b, float tolerance = 0.01f)
{
    return std::fabs(a - b) <= tolerance;
}
}

TEST_CASE("indoor water: waterAt inside, outside, at the top, two pieces")
{
    const std::vector<IndoorWaterVolume> volumes = pools();

    const std::optional<IndoorWaterSample> inside = indoorWaterAt(volumes, {}, 500.0f, 500.0f, -100.0f);
    REQUIRE(inside.has_value());
    CHECK(inside->volumeIndex == 0);
    CHECK(near(inside->surfaceZ, 0.0f));
    CHECK(near(inside->bottomZ, -400.0f));

    CHECK_FALSE(indoorWaterAt(volumes, {}, 500.0f, 500.0f, 0.0f).has_value());      // the surface itself is air
    CHECK(indoorWaterAt(volumes, {}, 500.0f, 500.0f, -0.01f).has_value());
    CHECK(indoorWaterAt(volumes, {}, 500.0f, 500.0f, -400.0f).has_value());         // the bottom is water
    CHECK_FALSE(indoorWaterAt(volumes, {}, 500.0f, 500.0f, -400.5f).has_value());
    CHECK_FALSE(indoorWaterAt(volumes, {}, 1000.5f, 500.0f, -100.0f).has_value());
    CHECK_FALSE(indoorWaterAt(volumes, {}, -1.0f, 500.0f, -100.0f).has_value());

    // The L: its second piece is shallower; the corner outside both pieces is dry.
    CHECK(indoorWaterAt(volumes, {}, 2100.0f, 100.0f, -250.0f)->volumeIndex == 1);
    CHECK(indoorWaterAt(volumes, {}, 2500.0f, 900.0f, -150.0f)->volumeIndex == 1);
    CHECK_FALSE(indoorWaterAt(volumes, {}, 2500.0f, 900.0f, -250.0f).has_value());
    CHECK_FALSE(indoorWaterAt(volumes, {}, 2500.0f, 100.0f, -100.0f).has_value());
}

TEST_CASE("indoor water: a moved top and the body column")
{
    const std::vector<IndoorWaterVolume> volumes = pools();
    const std::vector<float> lowered = {-300.0f, 0.0f};

    CHECK_FALSE(indoorWaterAt(volumes, lowered, 500.0f, 500.0f, -100.0f).has_value());
    const std::optional<IndoorWaterSample> low = indoorWaterAt(volumes, lowered, 500.0f, 500.0f, -350.0f);
    REQUIRE(low.has_value());
    CHECK(near(low->surfaceZ, -300.0f));

    // A body whose feet are under the surface touches the water; one standing on the surface does not.
    CHECK(indoorBodyWaterSample(volumes, {}, 500.0f, 500.0f, -10.0f, 160.0f).has_value());
    CHECK_FALSE(indoorBodyWaterSample(volumes, {}, 500.0f, 500.0f, 0.0f, 160.0f).has_value());
    CHECK(indoorBodyWaterSample(volumes, {}, 500.0f, 500.0f, -500.0f, 160.0f).has_value());
    CHECK_FALSE(indoorBodyWaterSample(volumes, {}, 500.0f, 500.0f, -700.0f, 160.0f).has_value());

    const std::optional<IndoorWaterSample> column = indoorWaterVolumeColumn(volumes, lowered, 0, 10.0f, 10.0f);
    REQUIRE(column.has_value());
    CHECK(near(column->surfaceZ, -300.0f));
    CHECK_FALSE(indoorWaterVolumeColumn(volumes, {}, 0, 1500.0f, 10.0f).has_value());
}

TEST_CASE("indoor water: a mover-bound top follows its door vertex")
{
    std::vector<IndoorWaterVolume> volumes = pools();
    volumes[0].moverVertexId = 1;
    std::vector<IndoorVertex> stored(3);
    stored[1].z = -77;
    std::vector<IndoorVertex> runtime = stored;
    runtime[1].z = -492;

    const std::vector<float> offsets = indoorWaterTopOffsets(volumes, stored, runtime);
    REQUIRE(offsets.size() == 2);
    CHECK(near(offsets[0], -415.0f));
    CHECK(near(offsets[1], 0.0f));
}

TEST_CASE("indoor water: scene water_volumes parse")
{
    const std::string yaml = R"(
- id: BlueWater0
  liquid: water
  pieces:
    - polygon: [[0, 0], [100, 0], [100, 100], [0, 100]]
      bottom: -400
      top: -50
  fog: {color_rgb: [0, 64, 128], near_distance: 0, far_distance: 1000}
  current: [10, 0, 0]
  mover_door_id: 7
- id: Lava
  liquid: lava
  pieces:
    - {polygon: [[0, 0], [10, 0], [0, 10]], bottom: 0, top: 5}
)";
    std::vector<IndoorWaterVolume> volumes;
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneWaterVolumes(yaml, volumes, error), error);
    REQUIRE(volumes.size() == 2);
    CHECK(volumes[0].id == "BlueWater0");
    CHECK(volumes[0].tint == std::array<float, 3>{0.0f, 0.5f, 0.7f});
    CHECK(volumes[0].fog.enabled);
    CHECK(near(volumes[0].fog.color[2], 128.0f / 255.0f));
    CHECK(near(volumes[0].current[0], 10.0f));
    CHECK(volumes[0].moverDoorId == 7u);
    CHECK(near(volumes[0].pieces[0].bounds[2], 100.0f));
    CHECK(volumes[1].liquid == IndoorLiquid::Lava);
    CHECK(volumes[1].tint == std::array<float, 3>{0.5f, 0.15f, 0.0f});
    CHECK_FALSE(volumes[1].fog.enabled);

    CHECK_FALSE(parseIndoorSceneWaterVolumes("- {id: a, pieces: [{polygon: [[0, 0], [1, 0]], bottom: 0, top: 1}]}",
        volumes, error));
    CHECK_FALSE(parseIndoorSceneWaterVolumes(
        "- {id: a, pieces: [{polygon: [[0, 0], [1, 0], [0, 1]], bottom: 1, top: 0}]}", volumes, error));
    CHECK_FALSE(parseIndoorSceneWaterVolumes(
        "- {id: a, depth: 3, pieces: [{polygon: [[0, 0], [1, 0], [0, 1]], bottom: 0, top: 1}]}", volumes, error));
    CHECK(error.find("depth") != std::string::npos);
    CHECK_FALSE(parseIndoorSceneWaterVolumes(
        "- {id: a, liquid: slime, pieces: [{polygon: [[0, 0], [1, 0], [0, 1]], bottom: 0, top: 1}]}", volumes,
        error));
}

TEST_CASE("indoor water: the swim state table")
{
    IndoorSwimMemory memory;

    // Dry, then falling in: the fall goes on until the eye is under.
    CHECK(indoorSwimState({false, false, true}, memory) == IndoorSwimState::Dry);
    CHECK(indoorSwimState({true, false, false}, memory) == IndoorSwimState::Falling);
    CHECK_FALSE(memory.wasSubmerged);
    CHECK(indoorSwimState({true, false, true}, memory) == IndoorSwimState::Wading);

    // Under, then out with the body still in: at the surface.
    CHECK(indoorSwimState({true, true, false}, memory) == IndoorSwimState::Submerged);
    CHECK(memory.wasSubmerged);
    CHECK(indoorSwimState({true, false, false}, memory) == IndoorSwimState::Surface);

    // A surface jump lasts until it lands or goes under; the eye under ends it.
    memory.surfaceJump = true;
    CHECK(indoorSwimState({true, false, false}, memory) == IndoorSwimState::SurfaceJump);
    CHECK(indoorSwimState({true, true, false}, memory) == IndoorSwimState::Submerged);
    CHECK_FALSE(memory.surfaceJump);
    memory.surfaceJump = true;
    CHECK(indoorSwimState({true, false, true}, memory) == IndoorSwimState::Wading);
    CHECK_FALSE(memory.surfaceJump);

    // On the bed with the eye under the party walks (MM9's WalkingInWater comes before UnderWater).
    CHECK(indoorSwimState({true, true, true}, memory) == IndoorSwimState::Bed);

    // Out of all water both bits clear: the next entry falls again.
    CHECK(indoorSwimState({false, false, false}, memory) == IndoorSwimState::Dry);
    CHECK_FALSE(memory.wasSubmerged);
    CHECK(indoorSwimState({true, false, false}, memory) == IndoorSwimState::Falling);
}

TEST_CASE("indoor water: swimming velocities")
{
    constexpr float Step = 1.0f / 128.0f;
    IndoorSwimInput input;

    // No input under water: MM9's idle sink, 40 LT/s.
    IndoorSwimVelocity velocity = indoorSwimVelocity(IndoorSwimState::Submerged, input, 1.0f, -50.0f, Step);
    CHECK(near(velocity.x, 0.0f));
    CHECK(near(velocity.z, -102.4f));

    // Forward follows the look direction, pitch included, at the swim speed.
    input.forward = 1.0f;
    input.yawRadians = 0.0f;
    input.pitchRadians = 0.5f;
    velocity = indoorSwimVelocity(IndoorSwimState::Submerged, input, 1.0f, -50.0f, Step);
    CHECK(near(velocity.x, 384.0f * std::cos(0.5f), 0.1f));
    CHECK(near(velocity.z, 384.0f * std::sin(0.5f), 0.1f));

    // Forward, strafe and up together are clamped to the swim speed; movement multipliers scale it.
    input.strafe = 1.0f;
    input.vertical = 1;
    input.pitchRadians = 0.0f;
    velocity = indoorSwimVelocity(IndoorSwimState::Submerged, input, 1.0f, -50.0f, Step);
    CHECK(near(std::sqrt(velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z), 384.0f, 0.1f));
    velocity = indoorSwimVelocity(IndoorSwimState::Submerged, input, 0.5f, -50.0f, Step);
    CHECK(near(std::sqrt(velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z), 192.0f, 0.1f));

    // Up and down alone: the world's vertical.
    input = {};
    input.vertical = -1;
    velocity = indoorSwimVelocity(IndoorSwimState::Submerged, input, 1.0f, -50.0f, Step);
    CHECK(near(velocity.z, -384.0f));

    // At the surface: looking up does not rise, and the eye point is held 1 unit over the water.
    input = {};
    input.forward = 1.0f;
    input.pitchRadians = 0.6f;
    velocity = indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 1.0f, Step);
    CHECK(near(velocity.x, 384.0f * std::cos(0.6f), 0.1f));
    CHECK(near(velocity.z, 0.0f));
    velocity = indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 2.0f, Step);
    CHECK(near(velocity.z, -128.0f, 0.1f));
    input.forward = 0.0f;
    velocity = indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 1.0f, Step);
    CHECK(near(velocity.z, 0.0f));       // no idle sink at the surface

    // Looking down while moving forward dives; Fly Down dives; Fly Up does nothing.
    input.forward = 1.0f;
    input.pitchRadians = -0.5f;
    velocity = indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 1.0f, Step);
    CHECK(velocity.z < -100.0f);
    input = {};
    input.vertical = -1;
    CHECK(indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 1.0f, Step).z < -300.0f);
    input.vertical = 1;
    CHECK(near(indoorSwimVelocity(IndoorSwimState::Surface, input, 1.0f, 1.0f, Step).z, 0.0f));

    // The surface jump's air control: forward 384, back and sideways 192.
    input = {};
    input.forward = 1.0f;
    CHECK(near(indoorSurfaceJumpAirControl(input, 1.0f).x, 384.0f));
    input.forward = -1.0f;
    CHECK(near(indoorSurfaceJumpAirControl(input, 1.0f).x, -192.0f));
    input.forward = 0.0f;
    input.strafe = 1.0f;
    CHECK(near(indoorSurfaceJumpAirControl(input, 1.0f).y, -192.0f));
}

TEST_CASE("indoor water: breath and drowning")
{
    IndoorBreathState breath;
    CHECK(near(indoorBreathFraction(breath), 1.0f));

    // 15 seconds of breath, then a tick every 2 seconds.
    CHECK(advanceIndoorBreath(breath, true, 7.5f) == 0);
    CHECK(near(indoorBreathFraction(breath), 0.5f));
    CHECK(advanceIndoorBreath(breath, true, 7.4f) == 0);
    CHECK(advanceIndoorBreath(breath, true, 0.2f) == 1);
    CHECK(near(indoorBreathFraction(breath), 0.0f));
    CHECK(advanceIndoorBreath(breath, true, 1.8f) == 0);
    CHECK(advanceIndoorBreath(breath, true, 0.2f) == 1);
    CHECK(advanceIndoorBreath(breath, true, 4.0f) == 2);

    // Out of the water it refills at once.
    CHECK(advanceIndoorBreath(breath, false, 0.01f) == 0);
    CHECK(near(indoorBreathFraction(breath), 1.0f));
    CHECK(advanceIndoorBreath(breath, true, 14.9f) == 0);

    // Each tick takes 1/6 of the maximum HP: six ticks from full to none.
    CHECK(indoorDrowningDamage(120) == 20);
    CHECK(indoorDrowningDamage(5) == 1);
}
