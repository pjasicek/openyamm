#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/maps/MapDeltaData.h"

using namespace OpenYAMM::Game;

namespace
{
uint16_t addVertex(IndoorMapData &mapData, int x, int y, int z)
{
    mapData.vertices.push_back({x, y, z});
    return static_cast<uint16_t>(mapData.vertices.size() - 1);
}

uint16_t addPortalFace(
    IndoorMapData &mapData,
    uint16_t sectorId,
    uint16_t backSectorId,
    int x,
    int minY,
    int maxY,
    int minZ,
    int maxZ)
{
    IndoorFace face = {};
    face.attributes = faceAttributeBit(FaceAttribute::IsPortal);
    face.roomNumber = sectorId;
    face.roomBehindNumber = backSectorId;
    face.facetType = 1;
    face.isPortal = true;
    face.vertexIndices = {
        addVertex(mapData, x, minY, minZ),
        addVertex(mapData, x, minY, maxZ),
        addVertex(mapData, x, maxY, maxZ),
        addVertex(mapData, x, maxY, minZ),
    };

    mapData.faces.push_back(std::move(face));
    const uint16_t faceId = static_cast<uint16_t>(mapData.faces.size() - 1);
    mapData.sectors[sectorId].portalFaceIds.push_back(faceId);
    mapData.sectors[sectorId].faceIds.push_back(faceId);
    mapData.sectors[backSectorId].portalFaceIds.push_back(faceId);
    mapData.sectors[backSectorId].faceIds.push_back(faceId);
    return faceId;
}

IndoorPortalVisibilityInput makeVisibilityInput(const IndoorMapData &mapData)
{
    IndoorPortalVisibilityInput input = {};
    input.pMapData = &mapData;
    input.pVertices = &mapData.vertices;
    input.cameraPosition = {0.0f, 0.0f, 0.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = 0;
    return input;
}

MapDeltaDoor makeDoorBlockingFace(uint32_t doorId, const std::vector<uint16_t> &vertexIds, uint16_t state)
{
    MapDeltaDoor door = {};
    door.doorId = doorId;
    door.state = state;
    door.moveLength = 100;
    door.openSpeed = 100;
    door.closeSpeed = 100;
    door.vertexIds = vertexIds;
    return door;
}
}

TEST_CASE("indoor portal visibility only traverses portals inside the camera frustum")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    addPortalFace(mapData, 0, 2, 100, 900, 980, -40, 40);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 3);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 0);
    CHECK_EQ(result.nodes.size(), 2);
}

TEST_CASE("indoor portal visibility traverses portal faces missing from sector portal lists")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    mapData.sectors[0].portalFaceIds.clear();
    mapData.sectors[0].faceIds.clear();
    mapData.sectors[1].portalFaceIds.clear();
    mapData.sectors[1].faceIds.clear();

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.acceptedPortalCount, 1);
}

TEST_CASE("indoor portal visibility carries narrowed portal frustum into child sectors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(4);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    addPortalFace(mapData, 1, 2, 200, -30, 30, -30, 30);
    addPortalFace(mapData, 1, 3, 200, 700, 780, -30, 30);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 4);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 1);
    CHECK_EQ(result.visibleSectorMask[3], 0);
}

TEST_CASE("indoor portal visibility keeps duplicate nodes for sectors seen through different portals")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    addPortalFace(mapData, 0, 1, 100, -45, -15, -40, 40);
    addPortalFace(mapData, 0, 1, 100, 15, 45, -40, 40);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.nodeIndicesBySector.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.nodeIndicesBySector[1].size(), 2);
}

TEST_CASE("indoor portal visibility traverses a portal from its back side")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.cameraPosition = {200.0f, 0.0f, 0.0f};
    input.cameraForward = {-1.0f, 0.0f, 0.0f};
    input.startSectorId = 1;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility traverses a north-south portal from both sides")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    IndoorFace face = {};
    face.attributes = faceAttributeBit(FaceAttribute::IsPortal);
    face.roomNumber = 0;
    face.roomBehindNumber = 1;
    face.facetType = 1;
    face.isPortal = true;
    face.vertexIndices = {
        addVertex(mapData, -40, 100, -40),
        addVertex(mapData, 40, 100, -40),
        addVertex(mapData, 40, 100, 40),
        addVertex(mapData, -40, 100, 40),
    };

    mapData.faces.push_back(std::move(face));
    const uint16_t faceId = static_cast<uint16_t>(mapData.faces.size() - 1);
    mapData.sectors[0].portalFaceIds.push_back(faceId);
    mapData.sectors[0].faceIds.push_back(faceId);
    mapData.sectors[1].portalFaceIds.push_back(faceId);
    mapData.sectors[1].faceIds.push_back(faceId);

    IndoorPortalVisibilityInput forwardInput = makeVisibilityInput(mapData);
    forwardInput.cameraForward = {0.0f, 1.0f, 0.0f};

    const IndoorPortalVisibilityResult forwardResult = buildIndoorPortalVisibility(forwardInput);

    REQUIRE_EQ(forwardResult.visibleSectorMask.size(), 2);
    CHECK_EQ(forwardResult.visibleSectorMask[0], 1);
    CHECK_EQ(forwardResult.visibleSectorMask[1], 1);

    IndoorPortalVisibilityInput backInput = makeVisibilityInput(mapData);
    backInput.cameraPosition = {0.0f, 200.0f, 0.0f};
    backInput.cameraForward = {0.0f, -1.0f, 0.0f};
    backInput.startSectorId = 1;

    const IndoorPortalVisibilityResult backResult = buildIndoorPortalVisibility(backInput);

    REQUIRE_EQ(backResult.visibleSectorMask.size(), 2);
    CHECK_EQ(backResult.visibleSectorMask[0], 1);
    CHECK_EQ(backResult.visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility includes frustum-visible unlinked geometry sectors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    addPortalFace(mapData, 0, 0, 1000, -40, 40, -40, 40);
    mapData.faces.clear();
    mapData.vertices.clear();
    mapData.sectors[0].portalFaceIds.clear();
    mapData.sectors[0].faceIds.clear();

    IndoorFace orphanFace = {};
    orphanFace.roomNumber = 1;
    orphanFace.roomBehindNumber = 0;
    orphanFace.facetType = 1;
    orphanFace.textureName = "orphan";
    orphanFace.vertexIndices = {
        addVertex(mapData, 100, -40, -40),
        addVertex(mapData, 100, 40, -40),
        addVertex(mapData, 100, 40, 40),
        addVertex(mapData, 100, -40, 40),
    };
    mapData.faces.push_back(std::move(orphanFace));
    mapData.sectors[1].faceIds.push_back(0);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility seeds linked sectors when starting inside unlinked geometry")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);

    addPortalFace(mapData, 1, 2, 100, -40, 40, -40, 40);

    mapData.sectors[1].minX = -64;
    mapData.sectors[1].maxX = 64;
    mapData.sectors[1].minY = -64;
    mapData.sectors[1].maxY = 64;
    mapData.sectors[1].minZ = -64;
    mapData.sectors[1].maxZ = 64;

    IndoorFace orphanFace = {};
    orphanFace.roomNumber = 0;
    orphanFace.roomBehindNumber = 0;
    orphanFace.facetType = 1;
    orphanFace.textureName = "orphan";
    orphanFace.vertexIndices = {
        addVertex(mapData, -10, -10, -10),
        addVertex(mapData, 10, -10, -10),
        addVertex(mapData, 10, 10, -10),
        addVertex(mapData, -10, 10, -10),
    };
    mapData.faces.push_back(std::move(orphanFace));
    mapData.sectors[0].faceIds.push_back(static_cast<uint16_t>(mapData.faces.size() - 1));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.startSectorId = 0;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 3);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 1);
}

TEST_CASE("indoor portal visibility blocks traversal through closed mechanism doors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        mapData.faces[faceId].vertexIndices,
        static_cast<uint16_t>(EvtMechanismState::Closed)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 0);
}

TEST_CASE("indoor portal visibility can ignore closed mechanism doors for interaction picking")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        mapData.faces[faceId].vertexIndices,
        static_cast<uint16_t>(EvtMechanismState::Closed)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;
    input.ignoreMechanismBlockers = true;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility allows traversal through open mechanism doors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        mapData.faces[faceId].vertexIndices,
        static_cast<uint16_t>(EvtMechanismState::Open)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility allows traversal through moving mechanism doors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        mapData.faces[faceId].vertexIndices,
        static_cast<uint16_t>(EvtMechanismState::Opening)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}
