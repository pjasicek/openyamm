#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorBakedLighting.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorMovers.h"
#include "game/maps/IndoorSceneYml.h"

#include <algorithm>
#include <cmath>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
// A leaf 100 wide and 200 tall in the plane y = 0, hinged at the origin about +z: closed along +x.
MapDeltaDoor leafDoor()
{
    MapDeltaDoor door;
    door.doorId = 7;
    door.moveLength = 900;
    door.openSpeed = 900;
    door.closeSpeed = 900;
    door.vertexIds = {0, 1, 2, 3};
    door.faceIds = {0};
    door.xOffsets = {0, 100, 100, 0};
    door.yOffsets = {0, 0, 0, 0};
    door.zOffsets = {0, 0, 200, 200};
    return door;
}

IndoorMoverDefinition leafMover(float openDegrees = 90.0f, bool openAway = false)
{
    IndoorMoverDefinition mover;
    mover.doorId = 7;
    IndoorMoverRotation rotation;
    rotation.openDegrees = openDegrees;
    rotation.openAway = openAway;
    mover.rotation = rotation;
    return mover;
}

std::vector<IndoorVertex> leafVertices()
{
    return {{0, 0, 0}, {100, 0, 0}, {100, 0, 200}, {0, 0, 200}};
}

// A shaft: a lower room (sector 1, floor at 0, up to 512) under an upper room (sector 2) whose floor at 512 has a hole
// 256 across, closed by a portal in the floor's plane.
IndoorMapData shaftThroughFloorPortal(int32_t upperSectorFlags)
{
    IndoorMapData map;
    map.vertices = {
        {-128, -128, 0}, {128, -128, 0}, {128, 128, 0}, {-128, 128, 0},
        {-128, -128, 512}, {128, -128, 512}, {128, 128, 512}, {-128, 128, 512},
        {-512, -512, 512}, {512, -512, 512}, {512, 512, 512}, {-512, 512, 512}};
    const auto floorFace = [](std::vector<uint16_t> vertices, uint16_t room)
    {
        IndoorFace face;
        face.vertexIndices = std::move(vertices);
        face.facetType = 3;
        face.roomNumber = face.roomBehindNumber = room;
        return face;
    };
    map.faces = {floorFace({0, 1, 2, 3}, 1), floorFace({8, 9, 5, 4}, 2), floorFace({9, 10, 6, 5}, 2),
        floorFace({10, 11, 7, 6}, 2), floorFace({11, 8, 4, 7}, 2), floorFace({4, 5, 6, 7}, 2)};
    IndoorFace &portal = map.faces.back();
    portal.isPortal = true;
    portal.attributes = static_cast<uint32_t>(FaceAttribute::IsPortal);
    portal.roomBehindNumber = 1;
    map.sectors.resize(3);
    IndoorSector &lower = map.sectors[1];
    lower.minX = lower.minY = -128;
    lower.maxX = lower.maxY = 128;
    lower.minZ = 0;
    lower.maxZ = 512;
    lower.floorFaceIds = {0};
    lower.portalFaceIds = {5};
    IndoorSector &upper = map.sectors[2];
    upper.flags = upperSectorFlags;
    upper.minX = upper.minY = -512;
    upper.maxX = upper.maxY = 512;
    upper.minZ = 512;
    upper.maxZ = 1024;
    upper.floorFaceIds = {1, 2, 3, 4};
    upper.portalFaceIds = {5};
    return map;
}

// Climbs straight up the shaft as the ladder step does; returns the foot height it reaches.
float climbShaft(const IndoorMapData &map)
{
    const IndoorMovementController controller(map, nullptr, nullptr);
    const IndoorBodyDimensions body = {};
    IndoorMoveState state;
    state.footZ = 1.0f;
    state.sectorId = 1;
    state.eyeSectorId = 1;

    for (int step = 0; step < 300; ++step)
    {
        state.verticalVelocity = 288.0f;
        state = controller.resolveMove(state, body, 0.0f, 0.0f, false, 1.0f / 128.0f, nullptr, std::nullopt, true,
            nullptr, true);
    }

    return state.footZ;
}

// A room (sector 1) with a floor at 0 and an overhang: a ceiling at 500 over everything west of x = 40.
IndoorMapData roomUnderOverhang()
{
    IndoorMapData map;
    map.vertices = {
        {-1024, -1024, 0}, {1024, -1024, 0}, {1024, 1024, 0}, {-1024, 1024, 0},
        {-1024, -1024, 500}, {40, -1024, 500}, {40, 1024, 500}, {-1024, 1024, 500}};
    IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = floor.roomBehindNumber = 1;
    IndoorFace ceiling;
    ceiling.vertexIndices = {7, 6, 5, 4};
    ceiling.facetType = 5;
    ceiling.roomNumber = ceiling.roomBehindNumber = 1;
    map.faces = {floor, ceiling};
    map.sectors.resize(2);
    IndoorSector &room = map.sectors[1];
    room.minX = room.minY = -1024;
    room.maxX = room.maxY = 1024;
    room.minZ = 0;
    room.maxZ = 1024;
    room.floorFaceIds = {0};
    room.ceilingFaceIds = {1};
    return map;
}

// Climbs the ladder with forward held as the party's ladder step does, from its foot; whether it reached the top.
bool climbLadder(const IndoorMapData &map, const IndoorLadder &ladder, float *pHighestFootZ = nullptr)
{
    const IndoorMovementController controller(map, nullptr, nullptr);
    const IndoorBodyDimensions body = {};
    const IndoorLadderFrame frame = indoorLadderFrame(ladder);
    const float holdDistance = body.radius + IndoorLadderHoldGap;
    IndoorMoveState state;
    state.x = ladder.bottom[0] - frame.facing.x * holdDistance;
    state.y = ladder.bottom[1] - frame.facing.y * holdDistance;
    state.footZ = ladder.bottom[2] + 1.0f;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    const float step = 1.0f / 128.0f;
    float highest = state.footZ;
    bool reachedTop = false;

    for (int index = 0; index < 1000 && !reachedTop; ++index)
    {
        const IndoorMoverBody moverBody = {state.x, state.y, state.footZ, body.radius, body.height};
        const IndoorLadderClimbStep climb =
            indoorLadderClimbStep(ladder, moverBody, frame.facing.x * 300.0f, frame.facing.y * 300.0f, 0, false, step);
        reachedTop = climb.exitTop;
        state.verticalVelocity = climb.verticalVelocity;
        state = controller.resolveMove(state, body, climb.velocityX, climb.velocityY, false, step, nullptr,
            std::nullopt, true, nullptr, true);
        highest = std::max(highest, state.footZ);
    }

    if (pHighestFootZ != nullptr)
    {
        *pHighestFootZ = highest;
    }

    return reachedTop;
}

std::vector<bx::Vec3> wallPolygon(float y)
{
    return {{-500.0f, y, 0.0f}, {500.0f, y, 0.0f}, {500.0f, y, 400.0f}, {-500.0f, y, 400.0f}};
}
}

TEST_CASE("rotating mover: closed at move_length, turned by the full angle at zero distance")
{
    const MapDeltaDoor door = leafDoor();
    const IndoorMoverDefinition mover = leafMover();
    std::vector<IndoorVertex> vertices = leafVertices();
    applyIndoorMechanismDoorToVertices(door, &mover, 900.0f, 1, vertices);
    CHECK(vertices[1].x == 100);
    CHECK(vertices[1].y == 0);
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, 1, vertices);
    CHECK(vertices[1].x == 0);
    CHECK(vertices[1].y == 100);
    CHECK(vertices[2].z == 200);
    applyIndoorMechanismDoorToVertices(door, &mover, 450.0f, 1, vertices);
    CHECK(vertices[1].x == 71);
    CHECK(vertices[1].y == 71);
}

TEST_CASE("rotating mover: the sign follows the axis and open-away direction only when asked")
{
    const MapDeltaDoor door = leafDoor();
    IndoorMoverDefinition mover = leafMover(-90.0f);
    std::vector<IndoorVertex> vertices = leafVertices();
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, 1, vertices);
    CHECK(vertices[1].y == -100);
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, -1, vertices);
    CHECK(vertices[1].y == -100);
    mover.rotation->openAway = true;
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, -1, vertices);
    CHECK(vertices[1].y == 100);
}

TEST_CASE("rotating mover: a linear door is unchanged by the shared pose function")
{
    MapDeltaDoor door = leafDoor();
    door.directionZ = -65536;
    door.moveLength = 256;
    std::vector<IndoorVertex> vertices = leafVertices();
    applyIndoorMechanismDoorToVertices(door, nullptr, 256.0f, 1, vertices);
    CHECK(vertices[0].z == -256);
    CHECK(vertices[2].z == -56);
    applyIndoorMechanismDoorToVertices(door, nullptr, 0.0f, 1, vertices);
    CHECK(vertices[2].z == 200);
}

TEST_CASE("rotating mover: sine easing is symmetric and continuous")
{
    CHECK(indoorMoverEase(IndoorMoverEasing::Sine, 0.0f) == doctest::Approx(0.0f));
    CHECK(indoorMoverEase(IndoorMoverEasing::Sine, 1.0f) == doctest::Approx(1.0f));
    CHECK(indoorMoverEase(IndoorMoverEasing::Sine, 0.5f) == doctest::Approx(0.5f));
    CHECK(indoorMoverEase(IndoorMoverEasing::Sine, 0.25f)
        == doctest::Approx(1.0f - indoorMoverEase(IndoorMoverEasing::Sine, 0.75f)));
    CHECK(indoorMoverEase(IndoorMoverEasing::Sine, 0.1f) < 0.1f);
    CHECK(indoorMoverEase(IndoorMoverEasing::Linear, 0.3f) == doctest::Approx(0.3f));
}

TEST_CASE("rotating mover: rigid motions invert and compose")
{
    IndoorMoverDefinition mover = leafMover();
    mover.rotation->pivot = {10.0f, 20.0f, 30.0f};
    mover.rotation->axis = {1.0f, 0.0f, 0.0f};
    const MapDeltaDoor door = leafDoor();
    const IndoorRigidMotion quarter = *indoorRotatingMoverMotion(door, &mover, 450.0f, 1);
    const IndoorRigidMotion half = *indoorRotatingMoverMotion(door, &mover, 0.0f, 1);
    const bx::Vec3 point = {50.0f, 60.0f, 70.0f};
    const bx::Vec3 moved = half.apply(point);
    const bx::Vec3 back = half.inverse().apply(moved);
    CHECK(back.x == doctest::Approx(point.x));
    CHECK(back.y == doctest::Approx(point.y));
    CHECK(back.z == doctest::Approx(point.z));
    const IndoorRigidMotion step = composeIndoorRigidMotions(half, quarter.inverse());
    const bx::Vec3 viaStep = step.apply(quarter.apply(point));
    CHECK(viaStep.x == doctest::Approx(moved.x));
    CHECK(viaStep.y == doctest::Approx(moved.y));
    CHECK(viaStep.z == doctest::Approx(moved.z));
}

TEST_CASE("rotating mover: open away swings from the party, a chord measures its travel")
{
    const MapDeltaDoor door = leafDoor();
    const IndoorMoverDefinition mover = leafMover(90.0f, true);
    // Positive angles swing the leaf toward +y.
    CHECK(indoorMoverOpenAwayDirection(door, mover, {50.0f, 300.0f, 80.0f}) == -1);
    CHECK(indoorMoverOpenAwayDirection(door, mover, {50.0f, -300.0f, 80.0f}) == 1);
    CHECK(indoorRotatingMoverMaxTravel(door, *mover.rotation) == doctest::Approx(141.42f).epsilon(0.01));
}

TEST_CASE("rotating mover: a body touches a polygon by its capsule and is moved clear of it")
{
    const IndoorMoverBody body = {0.0f, 30.0f, 0.0f, 37.0f, 160.0f};
    CHECK(indoorBodyTouchesPolygon(body, wallPolygon(0.0f)));
    CHECK_FALSE(indoorBodyTouchesPolygon(body, wallPolygon(100.0f)));
    const bx::Vec3 clear = indoorBodyPolygonClearance(body, wallPolygon(0.0f), {0.0f, 1.0f, 0.0f});
    CHECK(clear.y > 6.9f);
    CHECK(clear.y < 8.5f);
    CHECK(clear.x == doctest::Approx(0.0f));
    // An arm coming down over the body's head pushes it down, off its side of the plate.
    const std::vector<bx::Vec3> arm = {{-100.0f, -100.0f, 120.0f}, {100.0f, -100.0f, 120.0f}, {100.0f, 100.0f, 120.0f},
        {-100.0f, 100.0f, 120.0f}};
    const IndoorMoverBody under = {0.0f, 0.0f, 0.0f, 37.0f, 160.0f};
    const bx::Vec3 down = indoorBodyPolygonClearance(under, arm, {0.0f, 0.0f, -1.0f});
    CHECK(down.z < -39.0f);
    // A polygon cutting the axis is left on the hinted side.
    const IndoorMoverBody cut = {0.0f, 0.0f, 0.0f, 37.0f, 160.0f};
    const std::vector<bx::Vec3> plate = {{-100.0f, -100.0f, 80.0f}, {100.0f, -100.0f, 80.0f}, {100.0f, 100.0f, 80.0f},
        {-100.0f, 100.0f, 80.0f}};
    const bx::Vec3 up = indoorBodyPolygonClearance(cut, plate, {0.0f, 0.0f, 1.0f});
    CHECK(up.z > 79.0f);
}

TEST_CASE("mover bodies: a floor rising under a body carries it, a ceiling or a leaf coming at it stops")
{
    const auto reversed = [](const std::vector<bx::Vec3> &polygon)
    {
        return std::vector<bx::Vec3>(polygon.rbegin(), polygon.rend());
    };
    // Wound counter-clockwise from above: the normal points up.
    const auto square = [](float z)
    {
        return std::vector<bx::Vec3>{{-100.0f, -100.0f, z}, {100.0f, -100.0f, z}, {100.0f, 100.0f, z},
            {-100.0f, 100.0f, z}};
    };
    const IndoorMoverBody standing = {0.0f, 0.0f, 0.0f, 37.0f, 160.0f};
    // A pressure plate under the feet rising again: it approaches the capsule but lay beneath the feet.
    CHECK(indoorMoverFaceApproachesBody(standing, square(0.0f), square(2.0f)));
    CHECK_FALSE(indoorMoverFaceBlocksBody(standing, square(0.0f), square(2.0f)));
    CHECK_FALSE(indoorMoverFaceBlocksBody(standing, square(-1.5f), square(0.5f)));
    // A floor already above the feet (the body beside a lift that rose past them) stops.
    CHECK(indoorMoverFaceBlocksBody(standing, square(10.0f), square(12.0f)));
    // A crusher's underside (facing down) coming down on the head stops; the body is behind its top face.
    CHECK(indoorMoverFaceBlocksBody(standing, reversed(square(161.0f)), reversed(square(159.0f))));
    CHECK_FALSE(indoorMoverFaceBlocksBody(standing, square(161.0f), square(159.0f)));
    // A leaf facing the body (wallPolygon faces -y) closing on it stops; one moving away does not.
    const IndoorMoverBody beside = {0.0f, -30.0f, 0.0f, 37.0f, 160.0f};
    CHECK(indoorMoverFaceBlocksBody(beside, wallPolygon(20.0f), wallPolygon(0.0f)));
    CHECK_FALSE(indoorMoverFaceBlocksBody(beside, wallPolygon(0.0f), wallPolygon(20.0f)));
    // The body behind the leaf (inside the solid, the trailing edge of a grate sliding away) does not stop it.
    CHECK_FALSE(indoorMoverFaceBlocksBody(beside, reversed(wallPolygon(20.0f)), reversed(wallPolygon(0.0f))));
}

TEST_CASE("rotating mover: its faces sample the stored pose's lightmap in any pose")
{
    IndoorBakedLighting lighting;
    lighting.pages.resize(1);
    IndoorBakedLightingFace face;
    face.page = 0;
    face.uAxis = {0.01f, 0.0f, 0.0f, 0.25f};
    face.vAxis = {0.0f, 0.0f, 0.02f, 0.0f};
    lighting.faces = {face};
    IndoorFace mapFace;
    mapFace.vertexIndices = {0, 1, 2, 3};
    const MapDeltaDoor door = leafDoor();
    const IndoorMoverDefinition mover = leafMover();
    const IndoorRigidMotion motion = *indoorRotatingMoverMotion(door, &mover, 0.0f, 1);
    std::vector<IndoorVertex> vertices = leafVertices();
    const std::vector<IndoorVertex> stored = leafVertices();
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, 1, vertices);
    const IndoorBakedFaceLightmap lightmap =
        IndoorBakedLighting::faceLightmap(&lighting, true, 0, mapFace, true, vertices, stored, &motion);
    REQUIRE(lightmap.page == 0);
    const std::array<float, 2> uv = lightmap.uvAt(face, 0.0f, 100.0f, 200.0f);
    const std::array<float, 2> storedUv = face.uvAt(100.0f, 0.0f, 200.0f);
    CHECK(uv[0] == doctest::Approx(storedUv[0]));
    CHECK(uv[1] == doctest::Approx(storedUv[1]));
    const std::array<const MapDeltaDoor *, 1> doors = {&door};
    CHECK(indoorMoverFaceBakeable(mapFace, doors, &mover));
    MapDeltaDoor wide = door;
    wide.xOffsets = {0, 2000, 2000, 0};
    const std::array<const MapDeltaDoor *, 1> wideDoors = {&wide};
    CHECK_FALSE(indoorMoverFaceBakeable(mapFace, wideDoors, &mover));
}

TEST_CASE("rotating mover: the scene loader refuses a mover that is not rigid or whose numbers disagree")
{
    IndoorMapData map;
    map.vertices = leafVertices();
    map.vertices.push_back({0, 0, 400});
    IndoorFace face;
    face.vertexIndices = {0, 1, 2, 3};
    map.faces = {face};
    IndoorSceneDoor sceneDoor;
    sceneDoor.door = leafDoor();
    sceneDoor.mover = leafMover();
    std::vector<IndoorMoverDefinition> movers;
    std::string error;
    REQUIRE(buildIndoorMoverDefinitions({sceneDoor}, map, movers, error));
    REQUIRE(movers.size() == 1);
    map.moverDefinitions = movers;
    CHECK(findIndoorMoverDefinition(map, 7) != nullptr);
    CHECK(findIndoorMoverDefinition(map, 8) == nullptr);

    IndoorSceneDoor badLength = sceneDoor;
    badLength.door.moveLength = 800;
    CHECK_FALSE(buildIndoorMoverDefinitions({badLength}, map, movers, error));

    IndoorSceneDoor linearDirection = sceneDoor;
    linearDirection.door.directionZ = 65536;
    CHECK_FALSE(buildIndoorMoverDefinitions({linearDirection}, map, movers, error));

    IndoorSceneDoor notRigid = sceneDoor;
    notRigid.door.vertexIds = {0, 1, 2};
    notRigid.door.xOffsets = {0, 100, 100};
    notRigid.door.yOffsets = {0, 0, 0};
    notRigid.door.zOffsets = {0, 0, 200};
    CHECK_FALSE(buildIndoorMoverDefinitions({notRigid}, map, movers, error));

    IndoorSceneDoor badAxis = sceneDoor;
    badAxis.mover->rotation->axis = {0.0f, 0.0f, 2.0f};
    CHECK_FALSE(buildIndoorMoverDefinitions({badAxis}, map, movers, error));

    map.faces[0].isPortal = true;
    CHECK_FALSE(buildIndoorMoverDefinitions({sceneDoor}, map, movers, error));
}

TEST_CASE("spinning mover: turns about its pivot, then rides its door's linear travel")
{
    // A linear door 256 down (closed at move_length: the stored pose is the BLV's vertices) with a spin about +y
    // through (50, 0, 100), the leaf's centre in the stored pose.
    MapDeltaDoor door = leafDoor();
    door.directionZ = -65536;
    door.moveLength = 256;
    door.zOffsets = {256, 256, 456, 456};      // the offsets: the pose at distance 0, 256 above the stored one
    IndoorMoverDefinition mover;
    mover.doorId = 7;
    IndoorMoverSpin spin;
    spin.pivot = {50.0f, 0.0f, 100.0f};
    spin.axis = {0.0f, 1.0f, 0.0f};
    mover.spin = spin;
    std::vector<IndoorVertex> vertices = leafVertices();

    // no turn: the linear formula's pose
    applyIndoorMechanismDoorToVertices(door, &mover, 256.0f, 1, vertices, 0.0f);
    CHECK(vertices[1].x == 100);
    CHECK(vertices[1].z == 0);
    // half a turn in the stored pose: (100, 0, 0) about (50, 0, 100) goes to (0, 0, 200)
    applyIndoorMechanismDoorToVertices(door, &mover, 256.0f, 1, vertices, 180.0f);
    CHECK(vertices[1].x == 0);
    CHECK(vertices[1].z == 200);
    // the same turn carried 256 up by the door's travel (distance 0)
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, 1, vertices, 180.0f);
    CHECK(vertices[1].x == 0);
    CHECK(vertices[1].z == 456);
    // a door without a mover ignores a spin angle
    applyIndoorMechanismDoorToVertices(door, nullptr, 256.0f, 1, vertices, 90.0f);
    CHECK(vertices[1].x == 100);
    CHECK(vertices[1].z == 0);
}

TEST_CASE("spinning mover: a spin on a rotating door turns before the swing")
{
    const MapDeltaDoor door = leafDoor();
    IndoorMoverDefinition mover = leafMover();
    IndoorMoverSpin spin;
    spin.pivot = {50.0f, 0.0f, 100.0f};
    spin.axis = {0.0f, 1.0f, 0.0f};
    mover.spin = spin;
    std::vector<IndoorVertex> vertices = leafVertices();
    // the half turn takes (100, 0, 0) to (0, 0, 200); the open swing (90 about +z at the origin) leaves it there
    applyIndoorMechanismDoorToVertices(door, &mover, 0.0f, 1, vertices, 180.0f);
    CHECK(vertices[1].x == 0);
    CHECK(vertices[1].y == 0);
    CHECK(vertices[1].z == 200);
    // (0, 0, 0) goes to (100, 0, 200), then the swing to (0, 100, 200)
    CHECK(vertices[0].x == 0);
    CHECK(vertices[0].y == 100);
    CHECK(vertices[0].z == 200);
}

TEST_CASE("spinning mover: the speed ramps up and down, and a reversal stops first")
{
    IndoorMoverSpin spin;
    spin.spinUpSeconds = 1.0f;
    spin.spinDownSeconds = 4.0f;
    CHECK(indoorMoverSpinRateStep(spin, 0.0f, 1.0f, 0.5f) == doctest::Approx(0.5f));
    CHECK(indoorMoverSpinRateStep(spin, 0.5f, 1.0f, 1.0f) == doctest::Approx(1.0f));
    CHECK(indoorMoverSpinRateStep(spin, 1.0f, 0.0f, 1.0f) == doctest::Approx(0.75f));
    CHECK(indoorMoverSpinRateStep(spin, 0.1f, 0.0f, 1.0f) == doctest::Approx(0.0f));
    // reversed while turning forward: down to a stop at the spin-down pace, then up the other way
    CHECK(indoorMoverSpinRateStep(spin, 1.0f, -1.0f, 2.0f) == doctest::Approx(0.5f));
    CHECK(indoorMoverSpinRateStep(spin, 0.0f, -1.0f, 0.25f) == doctest::Approx(-0.25f));
    // no ramps: at once
    IndoorMoverSpin instant;
    CHECK(indoorMoverSpinRateStep(instant, 0.0f, 1.0f, 0.01f) == doctest::Approx(1.0f));
    CHECK(indoorMoverSpinRateStep(instant, 1.0f, -1.0f, 0.01f) == doctest::Approx(-1.0f));
    CHECK(indoorMoverSpinRateStep(instant, 1.0f, 0.0f, 0.01f) == doctest::Approx(0.0f));
}

TEST_CASE("spinning mover: the scene loader takes a spin on a linear door and refuses a bad one")
{
    IndoorMapData map;
    map.vertices = leafVertices();
    IndoorFace face;
    face.vertexIndices = {0, 1, 2, 3};
    map.faces = {face};
    IndoorSceneDoor sceneDoor;
    sceneDoor.door = leafDoor();
    sceneDoor.door.directionZ = -65536;
    sceneDoor.door.moveLength = 256;
    IndoorMoverDefinition mover;
    mover.doorId = 7;
    mover.spin = IndoorMoverSpin{};
    sceneDoor.mover = mover;
    std::vector<IndoorMoverDefinition> movers;
    std::string error;
    REQUIRE(buildIndoorMoverDefinitions({sceneDoor}, map, movers, error));
    REQUIRE(movers.size() == 1);
    CHECK(movers[0].spin.has_value());

    IndoorSceneDoor badAxis = sceneDoor;
    badAxis.mover->spin->axis = {0.0f, 2.0f, 0.0f};
    CHECK_FALSE(buildIndoorMoverDefinitions({badAxis}, map, movers, error));

    IndoorSceneDoor stopped = sceneDoor;
    stopped.mover->spin->degreesPerSecond = 0.0f;
    CHECK_FALSE(buildIndoorMoverDefinitions({stopped}, map, movers, error));

    IndoorSceneDoor notRigid = sceneDoor;
    notRigid.door.vertexIds = {0, 1, 2};
    notRigid.door.xOffsets = {0, 100, 100};
    notRigid.door.yOffsets = {0, 0, 0};
    notRigid.door.zOffsets = {0, 0, 200};
    CHECK_FALSE(buildIndoorMoverDefinitions({notRigid}, map, movers, error));
}

TEST_CASE("ladder: grabbing needs the body in front of the strip and moving toward it")
{
    IndoorLadder ladder;
    ladder.bottom = {0.0f, 0.0f, 0.0f};
    ladder.top = {0.0f, 0.0f, 600.0f};
    ladder.facingDegrees = 0.0f;
    ladder.width = 120.0f;
    ladder.reach = 48.0f;
    const IndoorMoverBody body = {-41.0f, 0.0f, 0.0f, 37.0f, 160.0f};
    CHECK(indoorLadderCanGrab(ladder, body, 300.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrab(ladder, body, -300.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrab(ladder, body, 0.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrab(ladder, {-400.0f, 0.0f, 0.0f, 37.0f, 160.0f}, 300.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrab(ladder, {-41.0f, 100.0f, 0.0f, 37.0f, 160.0f}, 300.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrab(ladder, {-41.0f, 0.0f, 700.0f, 37.0f, 160.0f}, 300.0f, 0.0f));
}

TEST_CASE("ladder: only a standing body grabs, unless the ladder takes a body in the air")
{
    IndoorLadder ladder;
    CHECK(indoorLadderGrabAllowed(ladder, true, false));
    CHECK_FALSE(indoorLadderGrabAllowed(ladder, false, false));
    CHECK_FALSE(indoorLadderGrabAllowed(ladder, true, true));
    ladder.grabInAir = true;
    CHECK(indoorLadderGrabAllowed(ladder, false, false));
    CHECK(indoorLadderGrabAllowed(ladder, true, false));
    CHECK_FALSE(indoorLadderGrabAllowed(ladder, false, true));
}

TEST_CASE("ladder: forward and the fly keys climb, the top exits, strafing past the strip lets go")
{
    IndoorLadder ladder;
    ladder.bottom = {0.0f, 0.0f, 0.0f};
    ladder.top = {0.0f, 0.0f, 600.0f};
    ladder.width = 120.0f;
    const float step = 1.0f / 128.0f;
    const IndoorMoverBody body = {-41.0f, 0.0f, 100.0f, 37.0f, 160.0f};
    IndoorLadderClimbStep climb = indoorLadderClimbStep(ladder, body, 300.0f, 0.0f, 0, false, step);
    CHECK(climb.verticalVelocity == doctest::Approx(IndoorLadderClimbSpeed));
    climb = indoorLadderClimbStep(ladder, body, -300.0f, 0.0f, 0, true, step);
    CHECK(climb.verticalVelocity == doctest::Approx(-IndoorLadderRunClimbSpeed));
    climb = indoorLadderClimbStep(ladder, body, 0.0f, 0.0f, 1, false, step);
    CHECK(climb.verticalVelocity > 0.0f);
    climb = indoorLadderClimbStep(ladder, body, 0.0f, 0.0f, 0, false, step);
    CHECK(climb.verticalVelocity == 0.0f);
    climb = indoorLadderClimbStep(ladder, {-41.0f, 0.0f, 598.0f, 37.0f, 160.0f}, 300.0f, 0.0f, 0, false, step);
    CHECK(climb.exitTop);
    climb = indoorLadderClimbStep(ladder, {-41.0f, 110.0f, 100.0f, 37.0f, 160.0f}, 0.0f, 300.0f, 0, false, step);
    CHECK(climb.detach);
    // A body off its hold distance is pulled back to it.
    climb = indoorLadderClimbStep(ladder, {-60.0f, 0.0f, 100.0f, 37.0f, 160.0f}, 0.0f, 0.0f, 0, false, step);
    CHECK(climb.velocityX > 0.0f);
}

TEST_CASE("ladder: an upright ladder's line is the vertical through its bottom")
{
    IndoorLadder ladder;
    ladder.bottom = {100.0f, -50.0f, 0.0f};
    ladder.top = {100.0f, -50.0f, 600.0f};
    CHECK_FALSE(indoorLadderLeans(ladder));
    const bx::Vec3 middle = indoorLadderLinePoint(ladder, 300.0f);
    CHECK(middle.x == 100.0f);
    CHECK(middle.y == -50.0f);
    CHECK(middle.z == 300.0f);
    CHECK(indoorLadderLinePoint(ladder, 900.0f).z == 600.0f);
    // No horizontal drift while climbing: only the hold and the strafe move it.
    const IndoorLadderClimbStep climb =
        indoorLadderClimbStep(ladder, {59.0f, -50.0f, 200.0f, 37.0f, 160.0f}, 300.0f, 0.0f, 0, false, 1.0f / 128.0f);
    CHECK(climb.verticalVelocity == doctest::Approx(IndoorLadderClimbSpeed));
    CHECK(climb.velocityX == doctest::Approx(0.0f));
    CHECK(climb.velocityY == doctest::Approx(0.0f));
}

TEST_CASE("ladder: a leaning ladder is grabbed at its foot and climbed along the line from bottom to top")
{
    IndoorLadder ladder;
    ladder.bottom = {0.0f, 0.0f, 0.0f};
    ladder.top = {300.0f, 0.0f, 600.0f};
    ladder.facingDegrees = 0.0f;
    ladder.width = 120.0f;
    CHECK(indoorLadderLeans(ladder));
    const bx::Vec3 middle = indoorLadderLinePoint(ladder, 300.0f);
    CHECK(middle.x == doctest::Approx(150.0f));
    CHECK(indoorLadderLinePoint(ladder, -20.0f).x == 0.0f);
    CHECK(indoorLadderLinePoint(ladder, 900.0f).x == doctest::Approx(300.0f));
    // The foot grabs as on an upright ladder; at mid height the strip is 150 further on.
    CHECK(indoorLadderCanGrab(ladder, {-41.0f, 0.0f, 0.0f, 37.0f, 160.0f}, 300.0f, 0.0f));
    const float step = 1.0f / 128.0f;
    // Held on the line at mid height, climbing moves it on along the line (half a unit per unit of height).
    IndoorLadderClimbStep climb =
        indoorLadderClimbStep(ladder, {109.0f, 0.0f, 300.0f, 37.0f, 160.0f}, 300.0f, 0.0f, 0, false, step);
    CHECK(climb.verticalVelocity == doctest::Approx(IndoorLadderClimbSpeed));
    CHECK(climb.velocityX == doctest::Approx(IndoorLadderClimbSpeed * 0.5f));
    climb = indoorLadderClimbStep(ladder, {109.0f, 0.0f, 300.0f, 37.0f, 160.0f}, -300.0f, 0.0f, 0, false, step);
    CHECK(climb.velocityX == doctest::Approx(-IndoorLadderClimbSpeed * 0.5f));
    // Measured from the foot (as an upright ladder would) this body is far behind the strip: the line holds it.
    climb = indoorLadderClimbStep(ladder, {109.0f, 0.0f, 300.0f, 37.0f, 160.0f}, 0.0f, 0.0f, 0, false, step);
    CHECK(climb.velocityX == doctest::Approx(0.0f));
    climb = indoorLadderClimbStep(ladder, {259.0f, 0.0f, 598.0f, 37.0f, 160.0f}, 300.0f, 0.0f, 0, false, step);
    CHECK(climb.exitTop);
}

TEST_CASE("ladder: a leaning ladder climbs out from under an overhang that stops an upright one")
{
    const IndoorMapData map = roomUnderOverhang();
    IndoorLadder upright;
    upright.bottom = {0.0f, 0.0f, 0.0f};
    upright.top = {0.0f, 0.0f, 700.0f};
    upright.width = 120.0f;
    float highest = 0.0f;
    CHECK_FALSE(climbLadder(map, upright, &highest));
    CHECK(highest < 500.0f - 150.0f);
    IndoorLadder leaning = upright;
    leaning.top = {350.0f, 0.0f, 700.0f};
    CHECK(climbLadder(map, leaning, &highest));
    CHECK(highest > 690.0f);
}

TEST_CASE("ladder: a grab_at_top ladder is taken at the edge by its top and climbed down by walking on")
{
    IndoorLadder ladder;
    ladder.bottom = {0.0f, 0.0f, 0.0f};
    ladder.top = {300.0f, 0.0f, 600.0f};
    ladder.facingDegrees = 0.0f;
    ladder.width = 120.0f;
    ladder.reach = 48.0f;
    // The exit is on a floor beside the top, to its left, far enough back that the party walks toward the edge first.
    ladder.topExit = {260.0f, 200.0f, 560.0f};
    const IndoorMoverBody atExit = {260.0f, 200.0f, 560.0f, 37.0f, 160.0f};
    ladder.grabAtTop = true;
    CHECK_FALSE(indoorLadderCanGrabAtTop(ladder, atExit, 0.0f, -300.0f));
    // Near the edge: within reach of the strip's top edge (here 40 back and 40 past its end).
    const IndoorMoverBody atEdge = {260.0f, 100.0f, 560.0f, 37.0f, 160.0f};
    ladder.grabAtTop = false;
    CHECK_FALSE(indoorLadderCanGrabAtTop(ladder, atEdge, 0.0f, -300.0f));
    ladder.grabAtTop = true;
    CHECK(indoorLadderCanGrabAtTop(ladder, atEdge, 0.0f, -300.0f));
    CHECK_FALSE(indoorLadderCanGrabAtTop(ladder, atEdge, 0.0f, 300.0f));
    CHECK_FALSE(indoorLadderCanGrabAtTop(ladder, atEdge, 0.0f, 0.0f));
    CHECK_FALSE(indoorLadderCanGrabAtTop(ladder, {260.0f, 100.0f, 300.0f, 37.0f, 160.0f}, 0.0f, -300.0f));
    // Held in front of the line just under the top, across from the body but a radius inside the strip's end.
    const bx::Vec3 hold = indoorLadderTopEntryPosition(ladder, atEdge);
    CHECK(hold.z == doctest::Approx(600.0f - IndoorLadderTopEntryDrop));
    CHECK(hold.x == doctest::Approx(292.0f - 41.0f));
    CHECK(hold.y == doctest::Approx(60.0f - 37.0f));
    CHECK(indoorLadderTopEntryPosition(ladder, {250.0f, 10.0f, 560.0f, 37.0f, 160.0f}).y == doctest::Approx(10.0f));
    // Walking on (away from the exit) descends along the line, walking back toward it climbs; neither strafes.
    const float step = 1.0f / 128.0f;
    const IndoorMoverBody held = {hold.x, hold.y, hold.z, 37.0f, 160.0f};
    IndoorLadderClimbStep climb = indoorLadderClimbStep(ladder, held, 0.0f, -300.0f, 0, false, step);
    CHECK(climb.verticalVelocity == doctest::Approx(-IndoorLadderClimbSpeed));
    CHECK(climb.velocityY == doctest::Approx(0.0f));
    CHECK_FALSE(climb.detach);
    climb = indoorLadderClimbStep(ladder, held, 0.0f, 300.0f, 0, false, step);
    CHECK(climb.verticalVelocity == doctest::Approx(IndoorLadderClimbSpeed));
    // Without grab_at_top the same input strafes along the strip, as before.
    ladder.grabAtTop = false;
    climb = indoorLadderClimbStep(ladder, held, 0.0f, -300.0f, 0, false, step);
    CHECK(climb.verticalVelocity == 0.0f);
    CHECK(climb.velocityY < 0.0f);
}

TEST_CASE("ladder: a climb passes a floor portal when the room above is marked for it")
{
    // The bug: over a hole the upper room has no floor face and the lower room ends at the portal, so a rising eye had
    // no sector and the move was refused about a body height under the portal.
    CHECK(climbShaft(shaftThroughFloorPortal(0)) < 512.0f - 64.0f);
    CHECK(climbShaft(shaftThroughFloorPortal(0x8)) > 512.0f + 100.0f);
}
