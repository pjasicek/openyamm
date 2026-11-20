#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/events/EventRuntime.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorPathfindingBuilder.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
constexpr uint32_t DoorMechanismId = 900042;
constexpr uint16_t DoorEventId = 30042;
constexpr uint8_t PolygonVerticalWall = 0x1;
constexpr uint8_t PolygonFloor = 0x3;
constexpr uint8_t PolygonCeiling = 0x5;
constexpr int FacePlaneScale = 65536;

// A door leaf standing on flat ground: 16 thick along x, 128 wide along y, 224 tall, hinged at its -y edge.
constexpr int DoorMinX = 1000;
constexpr int DoorMaxX = 1016;
constexpr int DoorMinY = -64;
constexpr int DoorMaxY = 64;
constexpr int DoorHeight = 224;

OutdoorBModelFace doorFace(std::vector<uint16_t> vertexIndices, int normalX, int normalY, int normalZ, uint8_t type)
{
    OutdoorBModelFace face = {};
    face.vertexIndices = std::move(vertexIndices);
    face.textureUs.assign(face.vertexIndices.size(), 0);
    face.textureVs.assign(face.vertexIndices.size(), 0);
    face.planeNormalX = normalX * FacePlaneScale;
    face.planeNormalY = normalY * FacePlaneScale;
    face.planeNormalZ = normalZ * FacePlaneScale;
    face.polygonType = type;
    face.attributes = faceAttributeBit(FaceAttribute::Clickable);
    face.cogTriggeredNumber = DoorEventId;
    face.textureName = "test_door";
    return face;
}

OutdoorBModel makeDoorLeaf()
{
    OutdoorBModel bmodel = {};
    bmodel.name = "TestDoor";
    bmodel.vertices = {
        {DoorMinX, DoorMinY, 0}, {DoorMaxX, DoorMinY, 0}, {DoorMaxX, DoorMaxY, 0}, {DoorMinX, DoorMaxY, 0},
        {DoorMinX, DoorMinY, DoorHeight}, {DoorMaxX, DoorMinY, DoorHeight},
        {DoorMaxX, DoorMaxY, DoorHeight}, {DoorMinX, DoorMaxY, DoorHeight}};
    bmodel.faces = {
        doorFace({0, 3, 7, 4}, -1, 0, 0, PolygonVerticalWall),
        doorFace({1, 5, 6, 2}, 1, 0, 0, PolygonVerticalWall),
        doorFace({0, 4, 5, 1}, 0, -1, 0, PolygonVerticalWall),
        doorFace({3, 2, 6, 7}, 0, 1, 0, PolygonVerticalWall),
        doorFace({4, 7, 6, 5}, 0, 0, 1, PolygonFloor),
        doorFace({0, 1, 2, 3}, 0, 0, -1, PolygonCeiling)};
    bmodel.minX = DoorMinX;
    bmodel.maxX = DoorMaxX;
    bmodel.minY = DoorMinY;
    bmodel.maxY = DoorMaxY;
    bmodel.maxZ = DoorHeight;
    bmodel.boundingCenterX = (DoorMinX + DoorMaxX) / 2;
    bmodel.boundingCenterZ = DoorHeight / 2;
    bmodel.boundingRadius = 160;
    return bmodel;
}

// A flat classic ODM (no scene profile, so classic_odm) holding only the door leaf and its rotating mechanism.
OutdoorMapData makeClassicMapWithDoor()
{
    OutdoorMapData mapData = {};
    mapData.fileName = "classic_door_test.odm";
    mapData.heightMap.assign(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight, 0);
    mapData.tileMap.assign(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight, 0);
    mapData.attributeMap.assign(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight, 0);
    mapData.bmodels.push_back(makeDoorLeaf());

    OutdoorBModelMechanism mechanism = {};
    mechanism.mechanismId = DoorMechanismId;
    mechanism.interactionEventId = DoorEventId;
    mechanism.sourceName = "TestDoor";
    mechanism.kind = OutdoorBModelMechanismKind::RotatingDoor;
    mechanism.motionKind = OutdoorBModelMechanismMotionKind::Rotation;
    mechanism.hasBModelBinding = true;
    mechanism.bmodelIndex = 0;
    mechanism.pivotX = (DoorMinX + DoorMaxX) / 2;
    mechanism.pivotY = DoorMinY;
    mechanism.rotationDegreesZ = 90.0f;
    mechanism.moveTimeMs = 500;
    mechanism.openAway = true;
    mapData.mechanisms.push_back(mechanism);
    return mapData;
}

std::string readSourceText(const std::string &relativePath)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    REQUIRE(file.good());
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}

struct ClassicDoorFixture
{
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader data;
    MapStatsEntry map = {};
    std::optional<OutdoorMapData> mapData;

    ClassicDoorFixture()
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
        REQUIRE(data.loadForHeadlessGameplay(assets));
        map.fileName = "classic_door_test.odm";
        mapData = makeClassicMapWithDoor();
    }

    void initialize(OutdoorWorldRuntime &world) const
    {
        world.initialize(map, data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(),
            data.getSpellTable(), data.getItemTable(), nullptr, nullptr, data.getStandardItemEnchantTable(),
            data.getSpecialItemEnchantTable(), &data.getChestTable(), mapData, std::nullopt, std::nullopt,
            EventRuntimeState{});
    }
};

std::vector<OutdoorFaceGeometryData> runtimeFaces(const OutdoorWorldRuntime &world)
{
    std::vector<OutdoorFaceGeometryData> faces;

    for (size_t faceIndex = 0; world.outdoorFace(faceIndex) != nullptr; ++faceIndex)
    {
        faces.push_back(*world.outdoorFace(faceIndex));
    }

    return faces;
}

// The door leaf's centre from the collision faces the world runtime holds.
bx::Vec3 doorCollisionCenter(const OutdoorWorldRuntime &world)
{
    bx::Vec3 sum = {0.0f, 0.0f, 0.0f};
    float count = 0.0f;

    for (const OutdoorFaceGeometryData &face : runtimeFaces(world))
    {
        for (const bx::Vec3 &vertex : face.vertices)
        {
            sum = bx::add(sum, vertex);
            count += 1.0f;
        }
    }

    REQUIRE(count > 0.0f);
    return bx::mul(sum, 1.0f / count);
}

// Whether an actor path along y = 0 through the doorway at x = 1008 is blocked, from the classic grid path map.
bool classicPathBlockedThroughDoorway(const OutdoorWorldRuntime &world, const OutdoorMapData &mapData)
{
    const std::vector<OutdoorFaceGeometryData> faces = runtimeFaces(world);
    OutdoorPathMapBuildResult result =
        OutdoorPathfindingBuilder::buildPathMap(mapData, nullptr, &faces, OutdoorPathMapBuildOptions{}, nullptr);
    CHECK_EQ(result.cookedNavigationFacetCount, 0u);
    return result.pathMap.traceLine({900.0f, 0.0f, 96.0f}, {1120.0f, 0.0f, 96.0f}).blocked;
}

void runMechanism(OutdoorWorldRuntime &world, float seconds)
{
    for (float elapsed = 0.0f; elapsed < seconds; elapsed += 0.05f)
    {
        world.updateWorld(0.05f);
    }
}
}

TEST_CASE("classic outdoor scenes accept typed mechanisms but keep destructibles and triggers BModel-world only")
{
    std::string sceneText = readSourceText("assets_dev/worlds/mm8/maps/out01.scene.yml");
    const size_t entitiesOffset = sceneText.find("entities:\n");
    REQUIRE(entitiesOffset != std::string::npos);
    sceneText.insert(
        entitiesOffset,
        "mechanisms:\n"
        "  - mechanism_id: 900042\n"
        "    event_id: 30042\n"
        "    source_object_index: 42\n"
        "    source_class: RotatingDoor\n"
        "    source_name: HutDoor\n"
        "    kind: rotating_door\n"
        "    binding:\n"
        "      target_kind: odm_bmodel\n"
        "      bmodel_index: 0\n"
        "      bmodel_name: HutDoor\n"
        "    motion:\n"
        "      rotation:\n"
        "        pivot_openyamm: {x: 1008, y: -64, z: 0}\n"
        "        rotation_angles_openyamm_deg: {x: 0, y: 0, z: 90}\n"
        "      move_time_ms: 1800\n"
        "    activation:\n"
        "      open_away: true\n");

    OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OutdoorSceneData> scene = sceneLoader.loadFromText(sceneText, sceneError);
    REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());
    CHECK(scene->sceneProfile == OutdoorSceneProfile::ClassicOdm);
    REQUIRE_EQ(scene->mechanisms.size(), 1u);
    CHECK(scene->mechanisms.front().kind == OutdoorBModelMechanismKind::RotatingDoor);
    CHECK(scene->mechanisms.front().motionKind == OutdoorBModelMechanismMotionKind::Rotation);
    CHECK(scene->mechanisms.front().openAway);

    OutdoorMapData mapData = {};
    mapData.bmodels.resize(1);

    for (const OutdoorSceneInteractiveFace &face : scene->interactiveFaces)
    {
        mapData.bmodels.resize(std::max(mapData.bmodels.size(), face.bmodelIndex + 1));
        mapData.bmodels[face.bmodelIndex].faces.resize(
            std::max(mapData.bmodels[face.bmodelIndex].faces.size(), face.faceIndex + 1));
    }

    for (const OutdoorSceneFaceAttributeOverride &face : scene->initialState.faceAttributeOverrides)
    {
        mapData.bmodels.resize(std::max(mapData.bmodels.size(), face.bmodelIndex + 1));
        mapData.bmodels[face.bmodelIndex].faces.resize(
            std::max(mapData.bmodels[face.bmodelIndex].faces.size(), face.faceIndex + 1));
    }

    MapDeltaData mapDeltaData = {};
    REQUIRE_MESSAGE(buildOutdoorMapStateFromScene(*scene, mapData, mapDeltaData, sceneError), sceneError.c_str());
    CHECK(mapData.sceneProfile == OutdoorSceneProfile::ClassicOdm);
    REQUIRE_EQ(mapData.mechanisms.size(), 1u);
    CHECK_EQ(mapData.mechanisms.front().mechanismId, 900042u);
    CHECK_EQ(mapData.mechanisms.front().interactionEventId, 30042u);

    OutdoorSceneData triggerScene = *scene;
    triggerScene.triggerVolumes.push_back({});
    CHECK_FALSE(buildOutdoorMapStateFromScene(triggerScene, mapData, mapDeltaData, sceneError));
    CHECK(sceneError.find("scene_profile bmodel_world") != std::string::npos);
}

TEST_CASE("classic outdoor rotating door moves collision and path geometry and survives a snapshot")
{
    ClassicDoorFixture fixture;
    OutdoorWorldRuntime world;
    fixture.initialize(world);

    EventRuntimeState *pEventRuntimeState = world.eventRuntimeState();
    REQUIRE(pEventRuntimeState != nullptr);
    REQUIRE(pEventRuntimeState->outdoorModelMechanisms.contains(DoorMechanismId));
    CHECK_EQ(pEventRuntimeState->outdoorModelMechanisms.at(DoorMechanismId).interactionEventId, DoorEventId);
    REQUIRE(pEventRuntimeState->mechanisms.contains(DoorMechanismId));
    CHECK_EQ(pEventRuntimeState->mechanisms.at(DoorMechanismId).state,
        static_cast<uint16_t>(EvtMechanismState::Closed));

    // Closed: the leaf blocks sight and the actor path through the doorway.
    const bx::Vec3 closedCenter = doorCollisionCenter(world);
    CHECK_EQ(closedCenter.x, doctest::Approx(1008.0f));
    CHECK_EQ(closedCenter.y, doctest::Approx(0.0f));
    CHECK_FALSE(world.hasClearOutdoorLineOfSight({900.0f, 0.0f, 96.0f}, {1120.0f, 0.0f, 96.0f}));
    CHECK(classicPathBlockedThroughDoorway(world, *fixture.mapData));

    // Open it as an event does: the party (at the origin, on the -x side) opens it, so it swings away to +x.
    EventRuntime::applyMechanismAction(
        pEventRuntimeState->mechanisms.at(DoorMechanismId), nullptr, MechanismAction::Open);
    pEventRuntimeState->lastAffectedMechanismIds.push_back(DoorMechanismId);
    world.applyEventRuntimeState();
    const int8_t openDirection = pEventRuntimeState->mechanisms.at(DoorMechanismId).rotationDirection;
    runMechanism(world, 1.0f);

    const RuntimeMechanismState &openState = pEventRuntimeState->mechanisms.at(DoorMechanismId);
    CHECK_EQ(openState.state, static_cast<uint16_t>(EvtMechanismState::Open));
    CHECK_FALSE(openState.isMoving);

    const bx::Vec3 openCenter = doorCollisionCenter(world);
    CHECK_EQ(openCenter.x, doctest::Approx(1072.0f).epsilon(0.01));
    CHECK_EQ(openCenter.y, doctest::Approx(-64.0f).epsilon(0.01));
    CHECK(world.hasClearOutdoorLineOfSight({900.0f, 0.0f, 96.0f}, {1120.0f, 0.0f, 96.0f}));
    CHECK_FALSE(classicPathBlockedThroughDoorway(world, *fixture.mapData));

    // A save restores the open state into a freshly loaded map: collision follows the restored state.
    const OutdoorWorldRuntime::Snapshot snapshot = world.snapshot();
    OutdoorWorldRuntime restoredWorld;
    fixture.initialize(restoredWorld);
    CHECK_EQ(doorCollisionCenter(restoredWorld).x, doctest::Approx(1008.0f));
    restoredWorld.restoreSnapshot(snapshot);

    const EventRuntimeState *pRestoredState = restoredWorld.eventRuntimeState();
    REQUIRE(pRestoredState != nullptr);
    REQUIRE(pRestoredState->mechanisms.contains(DoorMechanismId));
    CHECK_EQ(pRestoredState->mechanisms.at(DoorMechanismId).state, static_cast<uint16_t>(EvtMechanismState::Open));
    CHECK_EQ(pRestoredState->mechanisms.at(DoorMechanismId).rotationDirection, openDirection);
    const bx::Vec3 restoredCenter = doorCollisionCenter(restoredWorld);
    CHECK_EQ(restoredCenter.x, doctest::Approx(1072.0f).epsilon(0.01));
    CHECK_EQ(restoredCenter.y, doctest::Approx(-64.0f).epsilon(0.01));
    CHECK(restoredWorld.hasClearOutdoorLineOfSight({900.0f, 0.0f, 96.0f}, {1120.0f, 0.0f, 96.0f}));

    // Closing again restores the blocking leaf.
    EventRuntimeState *pWritableRestoredState = restoredWorld.eventRuntimeState();
    EventRuntime::applyMechanismAction(
        pWritableRestoredState->mechanisms.at(DoorMechanismId), nullptr, MechanismAction::Close);
    runMechanism(restoredWorld, 1.0f);
    CHECK_EQ(pWritableRestoredState->mechanisms.at(DoorMechanismId).state,
        static_cast<uint16_t>(EvtMechanismState::Closed));
    CHECK_EQ(doorCollisionCenter(restoredWorld).x, doctest::Approx(1008.0f));
    CHECK_FALSE(restoredWorld.hasClearOutdoorLineOfSight({900.0f, 0.0f, 96.0f}, {1120.0f, 0.0f, 96.0f}));
    CHECK(classicPathBlockedThroughDoorway(restoredWorld, *fixture.mapData));
}
