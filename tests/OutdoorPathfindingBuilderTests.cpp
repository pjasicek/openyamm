#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/outdoor/OutdoorPathfindingBuilder.h"
#include "game/pathfinding/PathPlanner.h"
#include "tests/RegressionMapLoader.h"

#include <cmath>
#include <cstddef>
#include <optional>
#include <vector>

using OpenYAMM::Game::FaceAttribute;
using OpenYAMM::Game::MapDeltaData;
using OpenYAMM::Game::MapBoundaryEdge;
using OpenYAMM::Game::MapBounds;
using OpenYAMM::Game::OutdoorBModel;
using OpenYAMM::Game::OutdoorBModelFace;
using OpenYAMM::Game::OutdoorMapData;
using OpenYAMM::Game::OutdoorMovementController;
using OpenYAMM::Game::OutdoorNavigationData;
using OpenYAMM::Game::OutdoorNavigationFacetKind;
using OpenYAMM::Game::OutdoorNavigationFacetReference;
using OpenYAMM::Game::OutdoorPathMapBuildOptions;
using OpenYAMM::Game::OutdoorPathMapBuildResult;
using OpenYAMM::Game::OutdoorPathTerrainMode;
using OpenYAMM::Game::OutdoorPathfindingBuilder;
using OpenYAMM::Game::OutdoorSupportKind;
using OpenYAMM::Game::OutdoorSceneProfile;
using OpenYAMM::Game::PathFacetKind;
using OpenYAMM::Game::PathFloorSample;
using OpenYAMM::Game::PathObject;
using OpenYAMM::Game::PathPlanRequest;
using OpenYAMM::Game::PathPlanResult;
using OpenYAMM::Game::PathPlanStatus;
using OpenYAMM::Game::PathPlanner;
using OpenYAMM::Game::PathPoint;
using OpenYAMM::Tests::regressionMapLoader;
using OpenYAMM::Tests::regressionMapLoaderFailure;
using OpenYAMM::Tests::regressionMapLoaderLoaded;
using OpenYAMM::Game::faceAttributeBit;
using OpenYAMM::Game::outdoorGridCornerWorldX;
using OpenYAMM::Game::outdoorGridCornerWorldY;
using OpenYAMM::Game::sampleOutdoorRenderedTerrainHeight;

namespace
{
constexpr uint8_t OutdoorPolygonWall = 0x1;
constexpr uint8_t OutdoorPolygonFloor = 0x3;
constexpr uint8_t OutdoorPolygonInBetweenFloorAndWall = 0x4;
constexpr uint8_t OutdoorPolygonCeiling = 0x5;
constexpr uint8_t OutdoorTerrainWater = 0x02;

size_t terrainSampleIndex(size_t gridX, size_t gridY)
{
    return gridY * static_cast<size_t>(OutdoorMapData::TerrainWidth) + gridX;
}

OutdoorMapData makeOutdoorMapWithTerrain()
{
    OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        static_cast<size_t>(OutdoorMapData::TerrainWidth) * static_cast<size_t>(OutdoorMapData::TerrainHeight),
        0);
    mapData.attributeMap.assign(mapData.heightMap.size(), 0);
    return mapData;
}

std::vector<uint8_t> makeOutdoorLandMask(uint8_t value = 1)
{
    return std::vector<uint8_t>(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
            * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1),
        value);
}

OutdoorBModelFace makeOutdoorFace(std::vector<uint16_t> vertexIndices, uint8_t polygonType, uint32_t attributes = 0)
{
    OutdoorBModelFace face = {};
    face.vertexIndices = std::move(vertexIndices);
    face.polygonType = polygonType;
    face.attributes = attributes;
    return face;
}

OutdoorBModel makePathTestBModel(uint32_t wallAttributes = 0)
{
    OutdoorBModel bModel = {};
    bModel.name = "path_test";
    bModel.vertices = {
        {-100, -100, 0},
        {100, -100, 0},
        {100, 100, 0},
        {-100, 100, 0},
        {0, -40, 0},
        {0, 40, 0},
        {0, 40, 120},
        {0, -40, 120}
    };
    bModel.faces = {
        makeOutdoorFace({0, 1, 2, 3}, OutdoorPolygonFloor),
        makeOutdoorFace({4, 5, 6, 7}, OutdoorPolygonWall, wallAttributes)
    };
    return bModel;
}

OutdoorBModel makeOutdoorPlannerBModel()
{
    OutdoorBModel bModel = {};
    bModel.name = "planner_test";
    bModel.vertices = {
        {-48, -120, 0},
        {192, -120, 0},
        {192, 120, 0},
        {-48, 120, 0},
        {72, -60, 0},
        {72, 60, 0},
        {72, 60, 120},
        {72, -60, 120}
    };
    bModel.faces = {
        makeOutdoorFace({0, 1, 2, 3}, OutdoorPolygonFloor),
        makeOutdoorFace({4, 5, 6, 7}, OutdoorPolygonWall)
    };
    return bModel;
}

OutdoorBModel makeOutdoorBridgeBModel(float centerX, float centerY, float z)
{
    OutdoorBModel bModel = {};
    bModel.name = "bridge_test";
    bModel.vertices = {
        {static_cast<int>(centerX - 192.0f), static_cast<int>(centerY - 192.0f), static_cast<int>(z)},
        {static_cast<int>(centerX + 192.0f), static_cast<int>(centerY - 192.0f), static_cast<int>(z)},
        {static_cast<int>(centerX + 192.0f), static_cast<int>(centerY + 192.0f), static_cast<int>(z)},
        {static_cast<int>(centerX - 192.0f), static_cast<int>(centerY + 192.0f), static_cast<int>(z)}
    };
    bModel.faces = {
        makeOutdoorFace({0, 1, 2, 3}, OutdoorPolygonFloor)
    };
    return bModel;
}

OutdoorMapData makeBModelStepTestMap(bool addOverheadFace)
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.noTerrain = true;

    OutdoorBModel bModel = {};
    bModel.name = "bmodel_step_test";
    bModel.vertices = {
        {-200, -100, 0},
        {0, -100, 0},
        {0, 100, 0},
        {-200, 100, 0},
        {-20, -100, 80},
        {200, -100, 80},
        {200, 100, 80},
        {-20, 100, 80},
        {0, -100, 0},
        {0, 100, 0},
        {0, 100, 80},
        {0, -100, 80},
        {-20, -100, 40},
        {200, -100, 40},
        {200, 100, 40},
        {-20, 100, 40},
    };
    bModel.faces = {
        makeOutdoorFace({0, 1, 2, 3}, OutdoorPolygonFloor),
        makeOutdoorFace({4, 5, 6, 7}, OutdoorPolygonFloor),
        makeOutdoorFace({8, 9, 10, 11}, OutdoorPolygonWall),
    };

    if (addOverheadFace)
    {
        bModel.faces.push_back(makeOutdoorFace({12, 15, 14, 13}, OutdoorPolygonCeiling));
    }

    mapData.bmodels.push_back(std::move(bModel));
    return mapData;
}

OpenYAMM::Game::OutdoorMoveState moveAcrossBModelStep(
    const OutdoorMovementController &controller,
    const OpenYAMM::Game::OutdoorBodyDimensions &body)
{
    OpenYAMM::Game::OutdoorMoveState state = controller.initializeStateForBody(-80.0f, 0.0f, 1.0f, body.radius);

    for (int step = 0; step < 80; ++step)
    {
        state = controller.resolveMoveForBody(
            state,
            body,
            384.0f,
            0.0f,
            0.0f,
            false,
            false,
            false,
            false,
            false,
            480.0f,
            1536.0f,
            4000.0f,
            1.0f / 128.0f);
    }

    return state;
}

OutdoorBModel makeOutdoorBridgeRampToFlatBModel(float centerX, float centerY)
{
    OutdoorBModel bModel = {};
    bModel.name = "bridge_ramp_to_flat_test";
    bModel.vertices = {
        {static_cast<int>(centerX - 192.0f), static_cast<int>(centerY - 128.0f), 80},
        {static_cast<int>(centerX), static_cast<int>(centerY - 128.0f), 160},
        {static_cast<int>(centerX), static_cast<int>(centerY + 128.0f), 160},
        {static_cast<int>(centerX - 192.0f), static_cast<int>(centerY + 128.0f), 80},
        {static_cast<int>(centerX), static_cast<int>(centerY - 128.0f), 160},
        {static_cast<int>(centerX + 384.0f), static_cast<int>(centerY - 128.0f), 160},
        {static_cast<int>(centerX + 384.0f), static_cast<int>(centerY + 128.0f), 160},
        {static_cast<int>(centerX), static_cast<int>(centerY + 128.0f), 160}
    };
    bModel.faces = {
        makeOutdoorFace({0, 1, 2, 3}, OutdoorPolygonInBetweenFloorAndWall),
        makeOutdoorFace({4, 5, 6, 7}, OutdoorPolygonFloor)
    };
    return bModel;
}

float bridgeRampHeightAt(float seamX, float x)
{
    return 80.0f + ((x - (seamX - 192.0f)) / 192.0f) * 80.0f;
}

PathObject makeOutdoorPathObject()
{
    PathObject object = {};
    object.radius = 8.0f;
    object.stepLength = 24.0f;
    object.stepHeight = 48.0f;
    return object;
}

PathPlanRequest makeOutdoorPathRequest()
{
    PathPlanRequest request = {};
    request.object = makeOutdoorPathObject();
    request.nodeLimit = 8000;
    return request;
}
}

TEST_CASE("outdoor BModel movement honors the configured body step height")
{
    const OutdoorMapData mapData = makeBModelStepTestMap(false);
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);

    const OpenYAMM::Game::OutdoorMoveState lowStep =
        moveAcrossBModelStep(controller, OpenYAMM::Game::OutdoorBodyDimensions{10.0f, 30.0f, 40.96f});
    const OpenYAMM::Game::OutdoorMoveState highStep =
        moveAcrossBModelStep(controller, OpenYAMM::Game::OutdoorBodyDimensions{10.0f, 30.0f, 128.0f});

    INFO("low step position=" << lowStep.x << "," << lowStep.y << "," << lowStep.footZ);
    INFO("high step position=" << highStep.x << "," << highStep.y << "," << highStep.footZ);
    CHECK_LT(lowStep.footZ, 40.0f);
    CHECK_GT(highStep.footZ, 80.0f);
}

TEST_CASE("outdoor BModel movement cannot step through an overhead face")
{
    const OutdoorMapData mapData = makeBModelStepTestMap(true);
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    const OpenYAMM::Game::OutdoorMoveState state =
        moveAcrossBModelStep(controller, OpenYAMM::Game::OutdoorBodyDimensions{10.0f, 30.0f, 128.0f});

    CHECK_LT(state.footZ, 40.0f);
}

TEST_CASE("outdoor actor leaving elevated support falls instead of snapping to terrain")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.bmodels.push_back(makeOutdoorBridgeBModel(0.0f, 0.0f, 160.0f));
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeActorStateForBodyPreservingZ(190.0f, 0.0f, 161.0f, 40.0f);
    REQUIRE_EQ(state.supportKind, OutdoorSupportKind::BModelFace);
    REQUIRE_FALSE(state.airborne);

    for (int tick = 0; tick < 16 && !state.airborne; ++tick)
    {
        const float previousZ = state.footZ;
        state = controller.resolveOutdoorActorMove(
            state, {40.0f, 128.0f}, 1000.0f, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
        CHECK(state.footZ >= previousZ - 1.0f);
    }
    REQUIRE(state.airborne);
    CHECK(state.footZ > 150.0f);

    for (int tick = 0; tick < 256 && state.airborne; ++tick)
    {
        state = controller.resolveOutdoorActorMove(
            state, {40.0f, 128.0f}, 384.0f, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
        CHECK(state.footZ >= 1.0f);
    }
    CHECK_FALSE(state.airborne);
    CHECK_EQ(state.supportKind, OutdoorSupportKind::Terrain);
    CHECK(state.footZ == doctest::Approx(1.0f));
    CHECK(state.verticalVelocity == doctest::Approx(0.0f));
}

TEST_CASE("outdoor actor retains ground adhesion across a small downward step")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.bmodels.push_back(makeOutdoorBridgeBModel(0.0f, 0.0f, 8.0f));
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeActorStateForBodyPreservingZ(190.0f, 0.0f, 9.0f, 40.0f);

    for (int tick = 0; tick < 16; ++tick)
    {
        state = controller.resolveOutdoorActorMove(
            state, {40.0f, 128.0f}, 1000.0f, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
        CHECK_FALSE(state.airborne);
    }
    CHECK_EQ(state.supportKind, OutdoorSupportKind::Terrain);
    CHECK(state.footZ == doctest::Approx(1.0f));
}

TEST_CASE("outdoor actor gravity accumulates while moving and while stationary")
{
    const OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    for (float horizontalVelocity : {0.0f, 384.0f})
    {
        OpenYAMM::Game::OutdoorMoveState state =
            controller.initializeActorStateForBodyPreservingZ(0.0f, 0.0f, 1000.0f, 40.0f);
        for (int tick = 0; tick < 128; ++tick)
        {
            state = controller.resolveOutdoorActorMove(
                state, {40.0f, 128.0f}, horizontalVelocity, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
        }
        CHECK(state.airborne);
        CHECK(state.footZ > 350.0f);
        CHECK(state.footZ < 360.0f);
        CHECK(state.verticalVelocity == doctest::Approx(-1280.0f));
    }
}

TEST_CASE("outdoor actor step checks the entire lift and destination body clearance")
{
    for (int ceilingZ : {40, 96, 112})
    {
        for (bool untouchable : {false, true})
        {
            OutdoorMapData mapData = makeBModelStepTestMap(true);
            mapData.bmodels[0].faces[2].vertexIndices = {8, 11, 10, 9};
            for (size_t vertexIndex = 12; vertexIndex < 16; ++vertexIndex)
            {
                mapData.bmodels[0].vertices[vertexIndex].z = ceilingZ;
            }
            if (untouchable)
            {
                mapData.bmodels[0].faces.back().attributes = faceAttributeBit(FaceAttribute::Untouchable);
            }
            const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
            OpenYAMM::Game::OutdoorMoveState state =
                controller.initializeActorStateForBodyPreservingZ(-80.0f, 0.0f, 1.0f, 10.0f);
            for (int tick = 0; tick < 80; ++tick)
            {
                state = controller.resolveOutdoorActorMove(
                    state, {10.0f, 30.0f, 128.0f}, 384.0f, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
            }
            INFO("ceiling=" << ceilingZ << " untouchable=" << untouchable);
            if (ceilingZ == 112 || untouchable)
            {
                CHECK(state.x > 100.0f);
                CHECK(state.footZ == doctest::Approx(81.0f));
            }
            else
            {
                CHECK(state.x < 0.0f);
                CHECK(state.footZ < 40.0f);
            }
        }
    }
}

TEST_CASE("outdoor actor step still honors body step height without overhead geometry")
{
    const OutdoorMapData mapData = makeBModelStepTestMap(false);
    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    for (float stepHeight : {40.0f, 128.0f})
    {
        OpenYAMM::Game::OutdoorMoveState state =
            controller.initializeActorStateForBodyPreservingZ(-80.0f, 0.0f, 1.0f, 10.0f);
        for (int tick = 0; tick < 80; ++tick)
        {
            state = controller.resolveOutdoorActorMove(
                state, {10.0f, 30.0f, stepHeight}, 384.0f, 0.0f, state.verticalVelocity, false, 1.0f / 128.0f);
        }
        if (stepHeight == 40.0f)
        {
            CHECK(state.footZ < 40.0f);
        }
        else
        {
            CHECK(state.footZ == doctest::Approx(81.0f));
        }
    }
}

TEST_CASE("outdoor actor step checks sloped and off-center overhead geometry across its radius")
{
    for (int obstruction = 0; obstruction < 4; ++obstruction)
    {
        OutdoorMapData mapData = makeBModelStepTestMap(true);
        OutdoorBModel &model = mapData.bmodels[0];
        model.faces[2].vertexIndices = {8, 11, 10, 9};
        if (obstruction == 0)
        {
            // Center clearance is 115, but the sloped ceiling enters the raised body's footprint.
            model.vertices[12].z = model.vertices[13].z = 65;
            model.vertices[14].z = model.vertices[15].z = 165;
        }
        else
        {
            const int nearY = obstruction == 3 ? 11 : 8;
            model.vertices[12] = {-20, nearY, 96};
            model.vertices[13] = {200, nearY, 96};
            model.vertices[14] = {200, 14, 96};
            model.vertices[15] = {-20, 14, 96};
            if (obstruction == 2)
            {
                // A suspended vertical face touches the raised body, but misses its initial height.
                model.vertices[12] = {-20, 8, 85};
                model.vertices[13] = {200, 8, 85};
                model.vertices[14] = {200, 8, 100};
                model.vertices[15] = {-20, 8, 100};
                model.faces.back().polygonType = OutdoorPolygonWall;
            }
        }

        const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
        // Start under the obstruction's footprint so this checks the lift itself, not later steering around it.
        const OpenYAMM::Game::OutdoorMoveState start =
            controller.initializeActorStateForBodyPreservingZ(-17.0f, 0.0f, 1.0f, 10.0f);
        const OpenYAMM::Game::OutdoorMoveState state = controller.resolveOutdoorActorMove(
            start, {10.0f, 30.0f, 128.0f}, 384.0f, 0.0f, 0.0f, false, 1.0f / 128.0f);
        INFO("obstruction=" << obstruction);
        if (obstruction == 3)
        {
            CHECK(state.footZ == doctest::Approx(81.0f));
        }
        else
        {
            CHECK(state.x < 0.0f);
            CHECK(state.footZ < 40.0f);
        }
    }
}

TEST_CASE("outdoor pathfinding builder materializes terrain triangles matching rendered terrain height")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.heightMap[terrainSampleIndex(64, 64)] = 1;
    mapData.heightMap[terrainSampleIndex(65, 64)] = 5;
    mapData.heightMap[terrainSampleIndex(64, 65)] = 9;
    mapData.heightMap[terrainSampleIndex(65, 65)] = 13;

    OutdoorPathMapBuildOptions options = {};
    options.includeBModels = false;
    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, options);

    REQUIRE_EQ(
        result.terrainTriangleCount,
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
            * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1) * 2);
    REQUIRE_EQ(result.pathFacetCount, result.terrainTriangleCount);

    const float firstTriangleX = outdoorGridCornerWorldX(64) + 128.0f;
    const float firstTriangleY = outdoorGridCornerWorldY(64) - 128.0f;
    const float firstExpectedHeight = sampleOutdoorRenderedTerrainHeight(mapData, firstTriangleX, firstTriangleY);
    const OpenYAMM::Game::PathFloorSample firstFloor =
        result.pathMap.floorAt({firstTriangleX, firstTriangleY, firstExpectedHeight + 256.0f});

    REQUIRE(firstFloor.hasFloor);
    CHECK_FALSE(firstFloor.inVoid);
    CHECK_GT(firstFloor.normalZ, 0.0f);
    CHECK(firstFloor.z == doctest::Approx(firstExpectedHeight));

    const float secondTriangleX = outdoorGridCornerWorldX(64) + 384.0f;
    const float secondTriangleY = outdoorGridCornerWorldY(64) - 384.0f;
    const float secondExpectedHeight = sampleOutdoorRenderedTerrainHeight(mapData, secondTriangleX, secondTriangleY);
    const OpenYAMM::Game::PathFloorSample secondFloor =
        result.pathMap.floorAt({secondTriangleX, secondTriangleY, secondExpectedHeight + 256.0f});

    REQUIRE(secondFloor.hasFloor);
    CHECK_FALSE(secondFloor.inVoid);
    CHECK_GT(secondFloor.normalZ, 0.0f);
    CHECK(secondFloor.z == doctest::Approx(secondExpectedHeight));
}

TEST_CASE("outdoor pathfinding builder can exclude water terrain from land-only maps")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.attributeMap[terrainSampleIndex(64, 64)] = OutdoorTerrainWater;

    OutdoorPathMapBuildOptions fullOptions = {};
    fullOptions.includeBModels = false;
    const OutdoorPathMapBuildResult fullResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, fullOptions);

    const float waterCellX = outdoorGridCornerWorldX(64) + 256.0f;
    const float waterCellY = outdoorGridCornerWorldY(64) - 256.0f;
    CHECK(fullResult.pathMap.floorAt({waterCellX, waterCellY, 256.0f}).hasFloor);

    OutdoorPathMapBuildOptions landOnlyOptions = {};
    landOnlyOptions.includeBModels = false;
    landOnlyOptions.terrainMode = OutdoorPathTerrainMode::LandOnly;
    const OutdoorPathMapBuildResult landOnlyResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, landOnlyOptions);

    CHECK_EQ(landOnlyResult.skippedWaterTerrainTriangleCount, 2u);
    CHECK_FALSE(landOnlyResult.pathMap.floorAt({waterCellX, waterCellY, 256.0f}).hasFloor);
}

TEST_CASE("outdoor pathfinding builder can route land actors around land-mask water")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    std::vector<uint8_t> landMask = makeOutdoorLandMask();
    constexpr size_t BarrierX = 64;

    for (size_t gridY = 62; gridY <= 66; ++gridY)
    {
        landMask[gridY * static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) + BarrierX] = 0;
    }

    OutdoorPathMapBuildOptions fullOptions = {};
    fullOptions.includeBModels = false;
    const OutdoorPathMapBuildResult fullResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, fullOptions, &landMask);

    const float waterCellX = outdoorGridCornerWorldX(static_cast<int>(BarrierX)) + 256.0f;
    const float waterCellY = outdoorGridCornerWorldY(64) - 256.0f;
    CHECK(fullResult.pathMap.floorAt({waterCellX, waterCellY, 256.0f}).hasFloor);

    OutdoorPathMapBuildOptions landOnlyOptions = {};
    landOnlyOptions.includeBModels = false;
    landOnlyOptions.terrainMode = OutdoorPathTerrainMode::LandOnly;
    const OutdoorPathMapBuildResult landOnlyResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, landOnlyOptions, &landMask);

    CHECK_EQ(landOnlyResult.skippedWaterTerrainTriangleCount, 10u);
    CHECK_FALSE(landOnlyResult.pathMap.floorAt({waterCellX, waterCellY, 256.0f}).hasFloor);

    PathPlanRequest request = makeOutdoorPathRequest();
    request.source = {
        outdoorGridCornerWorldX(static_cast<int>(BarrierX) - 1) + 256.0f,
        waterCellY,
        0.0f
    };
    request.target = {
        outdoorGridCornerWorldX(static_cast<int>(BarrierX) + 1) + 256.0f,
        waterCellY,
        0.0f
    };
    request.mapRevision = landOnlyResult.pathMap.revision();

    CHECK_FALSE(landOnlyResult.pathMap.canReachDirectly(request.source, request.target, request.object));

    PathPlanner planner;
    const PathPlanResult planResult = planner.plan(landOnlyResult.pathMap, request);

    REQUIRE(planResult.status == PathPlanStatus::Success);
    REQUIRE(planResult.waypoints.size() > 1);
    CHECK(planResult.waypoints.back().x == doctest::Approx(request.target.x));
    CHECK(planResult.waypoints.back().y == doctest::Approx(request.target.y));
}

TEST_CASE("outdoor land path can recover actor source from land-mask water")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    std::vector<uint8_t> landMask = makeOutdoorLandMask();
    constexpr size_t WaterX = 64;
    constexpr size_t WaterY = 64;
    landMask[WaterY * static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) + WaterX] = 0;

    OutdoorPathMapBuildOptions landOnlyOptions = {};
    landOnlyOptions.includeBModels = false;
    landOnlyOptions.terrainMode = OutdoorPathTerrainMode::LandOnly;
    const OutdoorPathMapBuildResult landOnlyResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, landOnlyOptions, &landMask);

    PathPlanRequest request = makeOutdoorPathRequest();
    request.source = {
        outdoorGridCornerWorldX(static_cast<int>(WaterX)) + 256.0f,
        outdoorGridCornerWorldY(static_cast<int>(WaterY)) - 256.0f,
        0.0f
    };
    request.target = {
        outdoorGridCornerWorldX(static_cast<int>(WaterX) - 1) + 256.0f,
        request.source.y,
        0.0f
    };
    request.mapRevision = landOnlyResult.pathMap.revision();
    request.sourceSnapDistance = static_cast<float>(OutdoorMapData::TerrainTileSize);

    PathPlanner planner;
    const PathPlanResult planResult = planner.plan(landOnlyResult.pathMap, request);

    CHECK(planResult.status == PathPlanStatus::Success);
    CHECK(planResult.debug.sourceValid);
    CHECK(planResult.debug.preferredSourceSnapUsed);
    const bool sourceSnappedAway =
        std::fabs(planResult.debug.snappedSource.x - request.source.x) > 0.001f
        || std::fabs(planResult.debug.snappedSource.y - request.source.y) > 0.001f;
    CHECK(sourceSnappedAway);
    REQUIRE_FALSE(planResult.waypoints.empty());
}

TEST_CASE("outdoor actor support query treats non-fluid BModel above water as bridge support")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.attributeMap[terrainSampleIndex(64, 64)] = OutdoorTerrainWater;
    const float bridgeX = outdoorGridCornerWorldX(64) + 256.0f;
    const float bridgeY = outdoorGridCornerWorldY(64) - 256.0f;
    constexpr float BridgeZ = 160.0f;
    mapData.bmodels.push_back(makeOutdoorBridgeBModel(bridgeX, bridgeY, BridgeZ));

    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    const OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeActorStateForBodyPreservingZ(bridgeX, bridgeY, BridgeZ + 1.0f, 37.0f);

    REQUIRE_EQ(state.supportKind, OutdoorSupportKind::BModelFace);
    CHECK_FALSE(state.supportIsFluid);
    CHECK(
        controller.hasNonFluidBModelActorSupport(
            state,
            37.0f,
            bridgeX,
            bridgeY,
            state.footZ,
            128.0f));
    CHECK_FALSE(
        controller.hasNonFluidBModelActorSupport(
            state,
            37.0f,
            bridgeX + 512.0f,
            bridgeY,
            state.footZ,
            128.0f));
}

TEST_CASE("outdoor map bounds clamp flying party movement and report the blocked edge")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    const MapBounds bounds = {
        .enabled = true,
        .minX = -23143,
        .maxX = 23143,
        .minY = -23143,
        .maxY = 23143,
    };
    const OutdoorMovementController controller(
        mapData,
        bounds,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    constexpr float PartyRadius = 37.0f;
    const float expectedMaxPartyX = static_cast<float>(bounds.maxX) - PartyRadius;
    OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeState(expectedMaxPartyX - 1.0f, 0.0f, 0.0f);
    state.footZ = 1000.0f;
    state.airborne = true;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState resolved = controller.resolveMove(
        state,
        1024.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        true,
        false,
        480.0f,
        1536.0f,
        4000.0f,
        0.1f);

    CHECK_EQ(resolved.x, doctest::Approx(expectedMaxPartyX));
    CHECK_EQ(resolved.y, doctest::Approx(0.0f));
    CHECK_EQ(resolved.footZ, doctest::Approx(1000.0f));
    const std::optional<MapBoundaryEdge> blockedEdge =
        controller.detectBoundaryBlock(state, resolved, 1024.0f, 0.0f);
    REQUIRE(blockedEdge.has_value());
    CHECK(*blockedEdge == MapBoundaryEdge::East);
}

TEST_CASE("outdoor actor placement initialization grounds a static source position immediately")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    const float actorX = outdoorGridCornerWorldX(64) + 256.0f;
    const float actorY = outdoorGridCornerWorldY(64) - 256.0f;
    constexpr float SourceFootZ = 129.0f;
    constexpr float ActorRadius = 37.0f;

    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    const OpenYAMM::Game::OutdoorMoveState preserved =
        controller.initializeActorStateForBodyPreservingZ(actorX, actorY, SourceFootZ, ActorRadius);
    const OpenYAMM::Game::OutdoorMoveState grounded =
        controller.initializeActorStateForBody(actorX, actorY, SourceFootZ, ActorRadius);

    CHECK(preserved.airborne);
    CHECK(preserved.footZ == doctest::Approx(SourceFootZ));
    CHECK_FALSE(grounded.airborne);
    CHECK_EQ(grounded.supportKind, OutdoorSupportKind::Terrain);
    CHECK(grounded.footZ == doctest::Approx(1.0f));
}

TEST_CASE("outdoor actor movement keeps BModel support across ramp to flat bridge seam")
{
    OutdoorMapData mapData = makeOutdoorMapWithTerrain();
    mapData.attributeMap[terrainSampleIndex(64, 64)] = OutdoorTerrainWater;
    const float seamX = outdoorGridCornerWorldX(64) + 256.0f;
    const float bridgeY = outdoorGridCornerWorldY(64) - 256.0f;
    mapData.bmodels.push_back(makeOutdoorBridgeRampToFlatBModel(seamX, bridgeY));

    const OutdoorMovementController controller(mapData, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    constexpr float ActorRadius = 37.0f;
    const float startX = seamX - 8.0f;
    const float startFootZ = bridgeRampHeightAt(seamX, startX) + 1.0f;
    const OpenYAMM::Game::OutdoorMoveState start =
        controller.initializeActorStateForBodyPreservingZ(startX, bridgeY, startFootZ, ActorRadius);

    REQUIRE_EQ(start.supportKind, OutdoorSupportKind::BModelFace);
    CHECK_EQ(start.supportFaceIndex, 0u);

    const OpenYAMM::Game::OutdoorMoveState resolved =
        controller.resolveOutdoorActorMove(
            start,
            OpenYAMM::Game::OutdoorBodyDimensions{ActorRadius, 128.0f},
            160.0f,
            0.0f,
            0.0f,
            false,
            0.1f);

    CHECK(resolved.x > seamX);
    CHECK_EQ(resolved.supportKind, OutdoorSupportKind::BModelFace);
    CHECK_EQ(resolved.supportFaceIndex, 1u);
    CHECK_FALSE(resolved.supportIsFluid);
    CHECK_FALSE(resolved.supportOnWater);
    CHECK(resolved.footZ == doctest::Approx(161.0f));
}

TEST_CASE("outdoor pathfinding builder converts BModel floors and walls into path facets")
{
    OutdoorMapData mapData = {};
    mapData.bmodels.push_back(makePathTestBModel());

    OutdoorPathMapBuildOptions options = {};
    options.includeTerrain = false;
    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, options);

    REQUIRE_EQ(result.sourceBModelFaceCount, 2u);
    REQUIRE_EQ(result.bModelPathFacetCount, 2u);
    REQUIRE_EQ(result.pathFacetCount, 2u);
    REQUIRE_EQ(result.pathMap.facets().size(), 2u);

    CHECK_EQ(result.pathMap.facets()[0].kind, PathFacetKind::Floor);
    CHECK(result.pathMap.facets()[0].walkableFloor);
    CHECK_EQ(result.pathMap.facets()[0].sourceId, OutdoorPathfindingBuilder::bModelSourceId(0, 0));
    CHECK_EQ(result.pathMap.facets()[1].kind, PathFacetKind::Wall);
    CHECK_FALSE(result.pathMap.facets()[1].walkableFloor);
    CHECK_EQ(result.pathMap.facets()[1].sourceId, OutdoorPathfindingBuilder::bModelSourceId(0, 1));
    CHECK(result.pathMap.floorAt({-50.0f, 0.0f, 64.0f}).hasFloor);
    CHECK_FALSE(
        result.pathMap.canReachDirectly(
            {-50.0f, 0.0f, 0.0f},
            {50.0f, 0.0f, 0.0f},
            makeOutdoorPathObject()));
}

TEST_CASE("outdoor pathfinding builder applies map delta face attributes to BModel blockers")
{
    OutdoorMapData mapData = {};
    mapData.bmodels.push_back(makePathTestBModel());

    MapDeltaData deltaData = {};
    deltaData.faceAttributes = {
        mapData.bmodels[0].faces[0].attributes,
        faceAttributeBit(FaceAttribute::Untouchable)
    };

    OutdoorPathMapBuildOptions options = {};
    options.includeTerrain = false;
    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, &deltaData, nullptr, options);

    REQUIRE_EQ(result.pathMap.facets().size(), 2u);
    CHECK(result.pathMap.facets()[1].attributes.untouchable);
    CHECK_FALSE(result.pathMap.facets()[1].blocking);
    CHECK(
        result.pathMap.canReachDirectly(
            {-50.0f, 0.0f, 0.0f},
            {50.0f, 0.0f, 0.0f},
            makeOutdoorPathObject()));
}

TEST_CASE("outdoor pathfinding builder feeds the generic planner around a BModel blocker")
{
    OutdoorMapData mapData = {};
    mapData.bmodels.push_back(makeOutdoorPlannerBModel());

    OutdoorPathMapBuildOptions options = {};
    options.includeTerrain = false;
    const OutdoorPathMapBuildResult buildResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, nullptr, options);

    PathPlanRequest request = makeOutdoorPathRequest();
    request.source = {0.0f, 0.0f, 0.0f};
    request.target = {144.0f, 0.0f, 0.0f};
    request.mapRevision = buildResult.pathMap.revision();

    CHECK_FALSE(buildResult.pathMap.canReachDirectly(request.source, request.target, request.object));

    PathPlanner planner;
    const PathPlanResult planResult = planner.plan(buildResult.pathMap, request);

    REQUIRE(planResult.status == PathPlanStatus::Success);
    REQUIRE(planResult.waypoints.size() > 1);
    CHECK(planResult.analyzedNodeCount > 0u);
    CHECK(planResult.waypoints.back().x == doctest::Approx(request.target.x));
    CHECK(planResult.waypoints.back().y == doctest::Approx(request.target.y));
}

TEST_CASE("new sorpigal bridge path exposes terrain to bridge route")
{
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());

    OpenYAMM::Game::GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "oute3.odm"));
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->outdoorMapData.has_value());

    OutdoorPathMapBuildOptions options = {};
    options.terrainMode = OutdoorPathTerrainMode::LandOnly;
    const OutdoorPathMapBuildResult buildResult =
        OutdoorPathfindingBuilder::buildPathMap(
            *selectedMap->outdoorMapData,
            selectedMap->outdoorMapDeltaData ? &*selectedMap->outdoorMapDeltaData : nullptr,
            nullptr,
            options,
            selectedMap->outdoorLandMask ? &*selectedMap->outdoorLandMask : nullptr);

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 128.0f;

    PathPlanRequest request = {};
    request.source = {-17420.1f, -7168.5f, 1.0f};
    request.target = {-16367.8f, -4737.73f, 353.0f};
    request.object = object;
    request.nodeLimit = 8000;
    request.mapRevision = buildResult.pathMap.revision();
    request.sourceSnapDistance = 512.0f;
    request.allowPartialPath = true;

    PathPlanner planner;
    const PathPlanResult planResult = planner.plan(buildResult.pathMap, request);

    bool routeUsesBModelRamp = false;
    bool routeReachesBridgeDeck = false;

    for (const PathPoint &waypoint : planResult.waypoints)
    {
        const PathFloorSample floor =
            buildResult.pathMap.floorAt({waypoint.x, waypoint.y, waypoint.z + 128.0f});

        if (!floor.hasFloor)
        {
            continue;
        }

        const int32_t sourceId = buildResult.pathMap.facets()[floor.facetIndex].sourceId;
        routeUsesBModelRamp = routeUsesBModelRamp || (sourceId >= 0 && floor.z > 0.0f && floor.z < 256.0f);
        routeReachesBridgeDeck =
            routeReachesBridgeDeck || (sourceId >= 0 && std::fabs(floor.z - 256.0f) < 0.01f);
    }

    REQUIRE(planResult.status == PathPlanStatus::Success);
    CHECK(routeUsesBModelRamp);
    CHECK(routeReachesBridgeDeck);
}

TEST_CASE("new sorpigal bridge lip path keeps ramp waypoints when direct handoff is disabled")
{
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());

    OpenYAMM::Game::GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "oute3.odm"));
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->outdoorMapData.has_value());

    OutdoorPathMapBuildOptions options = {};
    options.terrainMode = OutdoorPathTerrainMode::LandOnly;
    const OutdoorPathMapBuildResult buildResult =
        OutdoorPathfindingBuilder::buildPathMap(
            *selectedMap->outdoorMapData,
            selectedMap->outdoorMapDeltaData ? &*selectedMap->outdoorMapDeltaData : nullptr,
            nullptr,
            options,
            selectedMap->outdoorLandMask ? &*selectedMap->outdoorLandMask : nullptr);

    PathObject object = {};
    object.radius = 40.0f;
    object.stepLength = 64.0f;
    object.stepHeight = 128.0f;

    PathPlanRequest request = {};
    request.source = {-15118.1f, -4840.0f, 1.0f};
    request.target = {-15715.6f, -4717.21f, 353.0f};
    request.object = object;
    request.nodeLimit = 8000;
    request.mapRevision = buildResult.pathMap.revision();
    request.sourceSnapDistance = 512.0f;
    request.allowPartialPath = true;
    request.allowDirect = false;

    PathPlanner planner;
    const PathPlanResult planResult = planner.plan(buildResult.pathMap, request);

    bool routeUsesBModelRamp = false;
    bool routeReachesBridgeDeck = false;

    for (const PathPoint &waypoint : planResult.waypoints)
    {
        const PathFloorSample floor =
            buildResult.pathMap.floorAt({waypoint.x, waypoint.y, waypoint.z + 128.0f});

        if (!floor.hasFloor)
        {
            continue;
        }

        const int32_t sourceId = buildResult.pathMap.facets()[floor.facetIndex].sourceId;
        routeUsesBModelRamp = routeUsesBModelRamp || (sourceId >= 0 && floor.z > 0.0f && floor.z < 256.0f);
        routeReachesBridgeDeck =
            routeReachesBridgeDeck || (sourceId >= 0 && std::fabs(floor.z - 256.0f) < 0.01f);
    }

    REQUIRE(planResult.status == PathPlanStatus::Success);
    REQUIRE(planResult.waypoints.size() > 1u);
    CHECK(routeUsesBModelRamp);
    CHECK(routeReachesBridgeDeck);
}

TEST_CASE("new sorpigal bridge path terrain waypoint can step onto bridge ramp")
{
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());

    OpenYAMM::Game::GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "oute3.odm"));
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->outdoorMapData.has_value());

    const OutdoorMovementController controller(
        *selectedMap->outdoorMapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    constexpr float ActorRadius = 40.0f;
    OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeActorStateForBodyPreservingZ(-15108.0f, -4795.15f, 1.0f, ActorRadius);
    REQUIRE_EQ(state.supportKind, OutdoorSupportKind::Terrain);

    const float targetX = -15172.0f;
    const float targetY = -4731.15f;

    for (int step = 0; step < 80 && state.supportKind != OutdoorSupportKind::BModelFace; ++step)
    {
        const float deltaX = targetX - state.x;
        const float deltaY = targetY - state.y;
        const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
        REQUIRE(distance > 0.001f);
        const float velocityX = deltaX / distance * 420.0f;
        const float velocityY = deltaY / distance * 420.0f;

        state =
            controller.resolveOutdoorActorMove(
                state,
                OpenYAMM::Game::OutdoorBodyDimensions{ActorRadius, 128.0f},
                velocityX,
                velocityY,
                0.0f,
                false,
                1.0f / 128.0f);
    }

    CHECK_EQ(state.supportKind, OutdoorSupportKind::BModelFace);
    CHECK(state.footZ > 1.0f);
}

TEST_CASE("ravenshore house stairs move party onto bmodel support")
{
    REQUIRE_MESSAGE(regressionMapLoaderLoaded(), regressionMapLoaderFailure());

    OpenYAMM::Game::GameDataLoader gameDataLoader = regressionMapLoader().gameDataLoader;
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(regressionMapLoader().assetFileSystem, "out02.odm"));
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->outdoorMapData.has_value());

    const OutdoorMovementController controller(
        *selectedMap->outdoorMapData,
        selectedMap->outdoorLandMask,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state =
        controller.initializeState(12323.1f, -7892.64f, 1.0f);
    REQUIRE_EQ(state.supportKind, OutdoorSupportKind::Terrain);

    for (int step = 0; step < 256 && state.y < -7297.5f; ++step)
    {
        state =
            controller.resolveMove(
                state,
                3.68373f,
                383.982f,
                0.0f,
                false,
                false,
                false,
                false,
                false,
                512.0f,
                0.0f,
                4000.0f,
                1.0f / 128.0f);
    }

    INFO("final position=" << state.x << "," << state.y << "," << state.footZ
        << " support=" << static_cast<int>(state.supportKind)
        << " bmodel=" << state.supportBModelIndex
        << " face=" << state.supportFaceIndex);
    CHECK_EQ(state.supportKind, OutdoorSupportKind::BModelFace);
    CHECK(state.footZ > 1.0f);
}

TEST_CASE("BModel-world cooked navigation uses 64-bit face identity beyond the classic stride")
{
    constexpr size_t FaceIndex = 5000;
    OutdoorMapData mapData = {};
    mapData.sceneProfile = OutdoorSceneProfile::BModelWorld;
    mapData.noTerrain = true;
    mapData.bmodels.resize(1);
    mapData.bmodels[0].faces.resize(FaceIndex + 1);

    OutdoorNavigationData navigation = {};
    navigation.formatVersion = 1;
    OutdoorNavigationFacetReference reference = {};
    reference.sourceKey = OutdoorPathfindingBuilder::bModelSourceKey(0, FaceIndex);
    reference.bModelIndex = 0;
    reference.faceIndex = FaceIndex;
    reference.kind = OutdoorNavigationFacetKind::Floor;
    reference.walkable = true;
    navigation.facets.push_back(reference);
    mapData.navigationData = navigation;

    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};
    geometry.bModelIndex = 0;
    geometry.faceIndex = FaceIndex;
    geometry.polygonType = OutdoorPolygonFloor;
    geometry.isWalkable = true;
    geometry.hasPlane = true;
    geometry.normal = {0.0f, 0.0f, 1.0f};
    geometry.vertices = {
        {-64.0f, -64.0f, 0.0f},
        {64.0f, -64.0f, 0.0f},
        {64.0f, 64.0f, 0.0f},
        {-64.0f, 64.0f, 0.0f}
    };
    const std::vector<OpenYAMM::Game::OutdoorFaceGeometryData> geometries = {geometry};

    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &geometries);

    REQUIRE_EQ(result.pathMap.facets().size(), 1);
    CHECK_EQ(OutdoorPathfindingBuilder::bModelSourceId(0, FaceIndex), -1);
    CHECK_EQ(result.pathMap.facets()[0].sourceId, 0);
    CHECK(result.pathMap.facets()[0].walkableFloor);

    bool snapValid = false;
    const PathPoint snapped = result.pathMap.snapToWalkableSourceFacet(
        result.pathMap.facets()[0].sourceId,
        {0.0f, 0.0f, 20.0f},
        64.0f,
        snapValid);
    CHECK(snapValid);
    CHECK_EQ(snapped.z, doctest::Approx(0.0f));
}

TEST_CASE("BModel-world cooked navigation preserves stacked walkable floors")
{
    OutdoorMapData mapData = {};
    mapData.sceneProfile = OutdoorSceneProfile::BModelWorld;
    mapData.noTerrain = true;
    mapData.bmodels.resize(1);
    mapData.bmodels[0].faces.resize(2);

    OutdoorNavigationData navigation = {};
    navigation.formatVersion = 1;

    for (uint32_t faceIndex = 0; faceIndex < 2; ++faceIndex)
    {
        OutdoorNavigationFacetReference reference = {};
        reference.sourceKey = OutdoorPathfindingBuilder::bModelSourceKey(0, faceIndex);
        reference.faceIndex = faceIndex;
        reference.kind = OutdoorNavigationFacetKind::Floor;
        reference.walkable = true;
        navigation.facets.push_back(reference);
    }

    mapData.navigationData = navigation;
    std::vector<OpenYAMM::Game::OutdoorFaceGeometryData> geometries;

    for (size_t faceIndex = 0; faceIndex < 2; ++faceIndex)
    {
        const float z = static_cast<float>(faceIndex) * 256.0f;
        OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};
        geometry.faceIndex = faceIndex;
        geometry.isWalkable = true;
        geometry.hasPlane = true;
        geometry.normal = {0.0f, 0.0f, 1.0f};
        geometry.vertices = {
            {-64.0f, -64.0f, z},
            {64.0f, -64.0f, z},
            {64.0f, 64.0f, z},
            {-64.0f, 64.0f, z}
        };
        geometries.push_back(geometry);
    }

    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &geometries);

    REQUIRE_EQ(result.pathMap.facets().size(), 2);
    const PathFloorSample lowerFloor = result.pathMap.floorAt({0.0f, 0.0f, 100.0f});
    const PathFloorSample upperFloor = result.pathMap.floorAt({0.0f, 0.0f, 300.0f});
    REQUIRE(lowerFloor.hasFloor);
    REQUIRE(upperFloor.hasFloor);
    CHECK_EQ(lowerFloor.z, doctest::Approx(0.0f));
    CHECK_EQ(upperFloor.z, doctest::Approx(256.0f));
}

TEST_CASE("BModel-world cooked dynamic barriers follow mechanism geometry")
{
    OutdoorMapData mapData = {};
    mapData.sceneProfile = OutdoorSceneProfile::BModelWorld;
    mapData.bmodels.resize(1);
    mapData.bmodels[0].faces.resize(1);
    OutdoorNavigationData navigation = {};
    OutdoorNavigationFacetReference reference = {};
    reference.sourceKey = OutdoorPathfindingBuilder::bModelSourceKey(0, 0);
    reference.kind = OutdoorNavigationFacetKind::Barrier;
    reference.blocking = true;
    reference.dynamic = true;
    reference.mechanismId = 900001;
    navigation.facets.push_back(reference);
    mapData.navigationData = navigation;

    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};
    geometry.hasPlane = true;
    geometry.normal = {1.0f, 0.0f, 0.0f};
    geometry.vertices = {
        {0.0f, -100.0f, 0.0f},
        {0.0f, 100.0f, 0.0f},
        {0.0f, 100.0f, 160.0f},
        {0.0f, -100.0f, 160.0f}
    };
    std::vector<OpenYAMM::Game::OutdoorFaceGeometryData> geometries = {geometry};
    const PathObject object = {true, 20.0f, 24.0f, 40.0f};

    const OutdoorPathMapBuildResult closedResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &geometries);
    REQUIRE_EQ(closedResult.dynamicNavigationFacetCount, 1);
    CHECK_FALSE(closedResult.pathMap.canReachDirectly(
        {-80.0f, 0.0f, 40.0f},
        {80.0f, 0.0f, 40.0f},
        object));

    for (bx::Vec3 &vertex : geometries[0].vertices)
    {
        vertex.x += 300.0f;
    }

    const OutdoorPathMapBuildResult openResult =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &geometries);
    CHECK(openResult.pathMap.canReachDirectly(
        {-80.0f, 0.0f, 40.0f},
        {80.0f, 0.0f, 40.0f},
        object));
}

TEST_CASE("BModel-world cooked navigation merges marked coplanar triangle pairs")
{
    OutdoorMapData mapData = {};
    mapData.sceneProfile = OutdoorSceneProfile::BModelWorld;
    mapData.bmodels.resize(1);
    mapData.bmodels[0].faces.resize(2);
    OutdoorNavigationData navigation = {};

    for (uint32_t faceIndex = 0; faceIndex < 2; ++faceIndex)
    {
        OutdoorNavigationFacetReference reference = {};
        reference.sourceKey = OutdoorPathfindingBuilder::bModelSourceKey(0, faceIndex);
        reference.faceIndex = faceIndex;
        reference.kind = OutdoorNavigationFacetKind::Floor;
        reference.walkable = true;
        reference.pathSourceId = 0;
        reference.mergeLeaderOffset = faceIndex;
        navigation.facets.push_back(reference);
    }

    mapData.navigationData = navigation;
    OpenYAMM::Game::OutdoorFaceGeometryData first = {};
    first.hasPlane = true;
    first.isWalkable = true;
    first.normal = {0.0f, 0.0f, 1.0f};
    first.vertices = {{0.0f, 0.0f, 0.0f}, {100.0f, 0.0f, 0.0f}, {100.0f, 100.0f, 0.0f}};
    OpenYAMM::Game::OutdoorFaceGeometryData second = first;
    second.faceIndex = 1;
    second.vertices = {{0.0f, 0.0f, 0.0f}, {100.0f, 100.0f, 0.0f}, {0.0f, 100.0f, 0.0f}};
    const std::vector<OpenYAMM::Game::OutdoorFaceGeometryData> geometries = {first, second};

    const OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &geometries);

    CHECK_EQ(result.cookedNavigationFacetCount, 2);
    CHECK_EQ(result.pathFacetCount, 1);
    REQUIRE_EQ(result.pathMap.facets().size(), 1);
    CHECK_EQ(result.pathMap.facets()[0].vertices.size(), 4);
    CHECK(result.pathMap.floorAt({50.0f, 50.0f, 32.0f}).hasFloor);
}
