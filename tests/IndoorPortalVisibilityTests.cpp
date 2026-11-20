#include "doctest/doctest.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>

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

uint16_t addSolidDoorFace(
    IndoorMapData &mapData,
    int x,
    int minY,
    int maxY,
    int minZ,
    int maxZ)
{
    IndoorFace face = {};
    face.roomNumber = 0;
    face.roomBehindNumber = 0;
    face.facetType = 1;
    face.vertexIndices = {
        addVertex(mapData, x, minY, minZ),
        addVertex(mapData, x, minY, maxZ),
        addVertex(mapData, x, maxY, maxZ),
        addVertex(mapData, x, maxY, minZ),
    };

    mapData.faces.push_back(std::move(face));
    return static_cast<uint16_t>(mapData.faces.size() - 1);
}

void translateFaceVertices(std::vector<IndoorVertex> &vertices, const IndoorFace &face, int dx, int dy, int dz)
{
    for (uint16_t vertexId : face.vertexIndices)
    {
        if (vertexId >= vertices.size())
        {
            continue;
        }

        IndoorVertex &vertex = vertices[vertexId];
        vertex.x += dx;
        vertex.y += dy;
        vertex.z += dz;
    }
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

MapDeltaDoor makeDoorBlockingFace(
    uint32_t doorId,
    uint16_t portalFaceId,
    uint16_t solidFaceId,
    uint16_t state)
{
    MapDeltaDoor door = {};
    door.doorId = doorId;
    door.state = state;
    door.moveLength = 100;
    door.openSpeed = 100;
    door.closeSpeed = 100;
    door.faceIds.push_back(solidFaceId);
    door.faceIds.push_back(portalFaceId);
    return door;
}

float visibilityPlaneDistance(const IndoorVisibilityPlane &plane, const bx::Vec3 &point)
{
    return plane.normal.x * point.x + plane.normal.y * point.y + plane.normal.z * point.z + plane.distance;
}

bool sphereIntersectsFrustum(const bx::Vec3 &center, float radius, const IndoorVisibilityFrustum &frustum)
{
    for (const IndoorVisibilityPlane &plane : frustum)
    {
        if (visibilityPlaneDistance(plane, center) < -radius)
        {
            return false;
        }
    }

    return true;
}

bool sphereIntersectsAnyFrustum(
    const bx::Vec3 &center,
    float radius,
    const std::vector<IndoorVisibilityFrustum> &frustums)
{
    for (const IndoorVisibilityFrustum &frustum : frustums)
    {
        if (sphereIntersectsFrustum(center, radius, frustum))
        {
            return true;
        }
    }

    return false;
}

const IndoorPortalVisibilityTrace *findPortalTraceWithReason(
    const IndoorPortalVisibilityResult &result,
    const std::string &reason)
{
    for (const IndoorPortalVisibilityTrace &trace : result.portalTraces)
    {
        if (trace.reason == reason)
        {
            return &trace;
        }
    }

    return nullptr;
}

const IndoorPortalVisibilityTrace *findPortalTraceForFace(
    const IndoorPortalVisibilityResult &result,
    uint16_t faceId,
    const std::string &reason)
{
    for (const IndoorPortalVisibilityTrace &trace : result.portalTraces)
    {
        if (trace.faceId == faceId && trace.reason == reason)
        {
            return &trace;
        }
    }

    return nullptr;
}

const MapDeltaDoor *findDoorContainingFace(const MapDeltaData &mapDeltaData, uint16_t faceId)
{
    for (const MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (std::find(door.faceIds.begin(), door.faceIds.end(), faceId) != door.faceIds.end())
        {
            return &door;
        }
    }

    return nullptr;
}

const MapDeltaDoor *findDoorById(const MapDeltaData &mapDeltaData, uint32_t doorId)
{
    for (const MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (door.doorId == doorId)
        {
            return &door;
        }
    }

    return nullptr;
}

bx::Vec3 faceCenter(const IndoorMapData &mapData, uint16_t faceId)
{
    bx::Vec3 center = {0.0f, 0.0f, 0.0f};

    if (faceId >= mapData.faces.size())
    {
        return center;
    }

    const IndoorFace &face = mapData.faces[faceId];
    size_t pointCount = 0;

    for (uint16_t vertexId : face.vertexIndices)
    {
        if (vertexId >= mapData.vertices.size())
        {
            continue;
        }

        const IndoorVertex &vertex = mapData.vertices[vertexId];
        center.x += static_cast<float>(vertex.x);
        center.y += static_cast<float>(vertex.y);
        center.z += static_cast<float>(vertex.z);
        ++pointCount;
    }

    if (pointCount == 0)
    {
        return center;
    }

    const float reciprocalCount = 1.0f / static_cast<float>(pointCount);
    center.x *= reciprocalCount;
    center.y *= reciprocalCount;
    center.z *= reciprocalCount;
    return center;
}

bx::Vec3 sectorBoundsCenter(const IndoorMapData &mapData, uint16_t sectorId)
{
    if (sectorId >= mapData.sectors.size())
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const IndoorSector &sector = mapData.sectors[sectorId];
    return {
        (static_cast<float>(sector.minX) + static_cast<float>(sector.maxX)) * 0.5f,
        (static_cast<float>(sector.minY) + static_cast<float>(sector.maxY)) * 0.5f,
        (static_cast<float>(sector.minZ) + static_cast<float>(sector.maxZ)) * 0.5f
    };
}

bx::Vec3 rotateAroundZ(const bx::Vec3 &value, float radians)
{
    const float cosAngle = std::cos(radians);
    const float sinAngle = std::sin(radians);
    return {
        value.x * cosAngle - value.y * sinAngle,
        value.x * sinAngle + value.y * cosAngle,
        value.z
    };
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return {};
    }

    input.seekg(0, std::ios::end);
    const std::streamoff size = input.tellg();

    if (size <= 0)
    {
        return {};
    }

    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    input.seekg(0, std::ios::beg);
    input.read(reinterpret_cast<char *>(bytes.data()), size);
    return input ? bytes : std::vector<uint8_t>{};
}

std::string readTextFile(const std::filesystem::path &path)
{
    std::ifstream input(path);

    if (!input)
    {
        return {};
    }

    return std::string(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}
}

TEST_CASE("indoor portal visibility only traverses portals inside the camera frustum")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    addPortalFace(mapData, 0, 2, 100, 900, 980, -40, 40);

    SUBCASE("procedural geometry")
    {
    }
    SUBCASE("native export writes portal plane orientations")
    {
        const std::optional<std::vector<uint8_t>> bytes = IndoorMapDataWriter{}.buildBytes(mapData);
        REQUIRE(bytes);
        std::optional<IndoorMapData> loaded = IndoorMapDataLoader{}.loadFromBytes(*bytes);
        REQUIRE(loaded);
        mapData = std::move(*loaded);
        REQUIRE(mapData.faces[0].planeNormal);
        CHECK_EQ((*mapData.faces[0].planeNormal)[0], -65536);
    }

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 3);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 0);
    CHECK_EQ(result.nodes.size(), 2);
    REQUIRE_EQ(result.frustumsBySector.size(), 3);
    CHECK_EQ(result.frustumsBySector[0].size(), 1);
    CHECK_EQ(result.frustumsBySector[1].size(), 1);
    CHECK_EQ(result.frustumsBySector[2].size(), 0);
    CHECK(sphereIntersectsAnyFrustum({150.0f, 0.0f, 0.0f}, 8.0f, result.frustumsBySector[1]));
    CHECK_FALSE(sphereIntersectsAnyFrustum({150.0f, 900.0f, 0.0f}, 8.0f, result.frustumsBySector[1]));
}

TEST_CASE("indoor portal visibility clips the authored aperture without expanding to sector bounds")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);
    mapData.sectors[0].minX = 0;
    mapData.sectors[0].maxX = 512;
    mapData.sectors[0].minY = -128;
    mapData.sectors[0].maxY = 128;
    mapData.sectors[0].minZ = 224;
    mapData.sectors[0].maxZ = 480;
    mapData.sectors[1].minX = 512;
    mapData.sectors[1].maxX = 1024;
    mapData.sectors[1].minY = -128;
    mapData.sectors[1].maxY = 128;
    mapData.sectors[1].minZ = 224;
    mapData.sectors[1].maxZ = 480;

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 512, -1, 1, 224, 480);

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.cameraPosition = {0.0f, -420.0f, 352.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 0);
    CHECK(findPortalTraceForFace(result, faceId, "clipped_portal") != nullptr);

    input.cameraPosition.y = 0.0f;
    const IndoorPortalVisibilityResult facingOpening = buildIndoorPortalVisibility(input);
    CHECK_EQ(facingOpening.visibleSectorMask[1], 1);
}

TEST_CASE("cd1 sector 101 sees sector 88 through diagonal floor-strip portal")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "cd1.blv");

    REQUIRE_FALSE(mapBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    constexpr uint16_t SourceSectorId = 101;
    constexpr uint16_t TargetSectorId = 88;
    constexpr uint16_t PortalFaceId = 2248;

    REQUIRE_GT(mapData->sectors.size(), SourceSectorId);
    REQUIRE_GT(mapData->sectors.size(), TargetSectorId);
    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, SourceSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, TargetSectorId);

    IndoorFaceGeometryCache geometryCache(mapData->faces.size());
    const IndoorFaceGeometryData *pPortalGeometry =
        geometryCache.geometryForFace(*mapData, mapData->vertices, PortalFaceId);
    REQUIRE(pPortalGeometry != nullptr);
    REQUIRE(pPortalGeometry->hasPlane);
    CHECK_LT(pPortalGeometry->maxZ - pPortalGeometry->minZ, 2.0f);
    CHECK_GT(pPortalGeometry->normal.z, -0.1f);
    CHECK_LT(pPortalGeometry->normal.z, 0.1f);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    const bx::Vec3 portalCenter = faceCenter(*mapData, PortalFaceId);
    const bx::Vec3 targetSectorCenter = sectorBoundsCenter(*mapData, TargetSectorId);
    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &mapData->vertices;
    input.cameraPosition = {
        portalCenter.x + pPortalGeometry->normal.x * 320.0f,
        portalCenter.y + pPortalGeometry->normal.y * 320.0f,
        352.0f
    };
    input.cameraForward = {
        targetSectorCenter.x - input.cameraPosition.x,
        targetSectorCenter.y - input.cameraPosition.y,
        0.0f
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 16.0f / 9.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), SourceSectorId);
    REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
    CHECK_EQ(result.visibleSectorMask[SourceSectorId], 1);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    CHECK(findPortalTraceForFace(result, PortalFaceId, "clipped_portal") == nullptr);
    const IndoorPortalVisibilityTrace *pAcceptedTrace =
        findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->sourceSectorId, SourceSectorId);
    CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);
}

TEST_CASE("d19 necromancer guild side room stays visible through open sector 3 doors")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm8" / "maps" / "d19.blv");
    const std::string sceneText =
        readTextFile(sourceRoot / "assets_dev" / "worlds" / "mm8" / "maps" / "d19.scene.yml");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(sceneText.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    SUBCASE("original map")
    {
    }
    SUBCASE("exported and reloaded map retains the collapsed portal plane")
    {
        const std::optional<std::vector<uint8_t>> exported = IndoorMapDataWriter{}.buildBytes(*mapData);
        REQUIRE(exported);
        mapData = mapDataLoader.loadFromBytes(*exported);
        REQUIRE(mapData);
    }

    std::string sceneError;
    const IndoorSceneYmlLoader sceneLoader = {};
    std::optional<IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData, sceneError);

    MapDeltaData mapDeltaData = {};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*sceneData, *mapData, mapDeltaData, sceneError), sceneError);

    constexpr uint16_t SourceSectorId = 2;
    constexpr uint16_t TargetSectorId = 3;
    constexpr uint16_t PortalFaceId = 3772;
    constexpr uint16_t LobbySectorId = 1;
    constexpr uint16_t LobbyPortalFaceId = 258;
    constexpr uint32_t LeftDoorId = 61;
    constexpr uint32_t RightDoorId = 62;

    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, SourceSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, TargetSectorId);
    REQUIRE(portalFace.planeNormal);
    CHECK_EQ((*portalFace.planeNormal)[0], 0);
    CHECK_EQ((*portalFace.planeNormal)[1], -65536);
    CHECK_EQ((*portalFace.planeNormal)[2], 0);
    REQUIRE_LT(LobbyPortalFaceId, mapData->faces.size());
    const IndoorFace &lobbyPortalFace = mapData->faces[LobbyPortalFaceId];
    REQUIRE_EQ(lobbyPortalFace.roomNumber, LobbySectorId);
    REQUIRE_EQ(lobbyPortalFace.roomBehindNumber, SourceSectorId);

    const MapDeltaDoor *pLeftDoor = findDoorById(mapDeltaData, LeftDoorId);
    const MapDeltaDoor *pRightDoor = findDoorById(mapDeltaData, RightDoorId);
    REQUIRE(pLeftDoor != nullptr);
    REQUIRE(pRightDoor != nullptr);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState leftDoorState = {};
    leftDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    leftDoorState.currentDistance = 0.0f;
    eventRuntimeState->mechanisms[LeftDoorId] = leftDoorState;

    RuntimeMechanismState rightDoorState = {};
    rightDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    rightDoorState.currentDistance = 0.0f;
    eventRuntimeState->mechanisms[RightDoorId] = rightDoorState;

    const std::vector<IndoorVertex> adjustedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &mapDeltaData, &*eventRuntimeState);

    const bx::Vec3 portalCenter = faceCenter(*mapData, PortalFaceId);
    const bx::Vec3 cameraPosition = {
        portalCenter.x - 320.0f,
        portalCenter.y - 256.0f,
        portalCenter.z
    };
    const bx::Vec3 baseForward = {
        portalCenter.x - cameraPosition.x,
        portalCenter.y - cameraPosition.y,
        portalCenter.z - cameraPosition.z
    };
    const float yawOffsets[] = {-0.08f, -0.04f, 0.0f, 0.04f, 0.08f};

    for (float yawOffset : yawOffsets)
    {
        IndoorPortalVisibilityInput input = {};
        input.pMapData = &*mapData;
        input.pPortalGraph = &portalGraph;
        input.pVertices = &adjustedVertices;
        input.pMapDeltaData = &mapDeltaData;
        input.pEventRuntimeState = &eventRuntimeState;
        input.cameraPosition = cameraPosition;
        input.cameraForward = rotateAroundZ(baseForward, yawOffset);
        input.cameraUp = {0.0f, 0.0f, 1.0f};
        input.verticalFovDegrees = 60.0f;
        input.aspectRatio = 16.0f / 9.0f;
        input.startSectorId = SourceSectorId;

        const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

        INFO("yawOffset=" << yawOffset);
        REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
        CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
        CHECK(findPortalTraceForFace(result, PortalFaceId, "child_frustum_small") == nullptr);
        const IndoorPortalVisibilityTrace *pAcceptedTrace =
            findPortalTraceForFace(result, PortalFaceId, "accepted");
        REQUIRE(pAcceptedTrace != nullptr);
        CHECK_EQ(pAcceptedTrace->sourceSectorId, SourceSectorId);
        CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);

    }

    const bx::Vec3 lobbyPortalCenter = faceCenter(*mapData, LobbyPortalFaceId);
    bool foundBackChain = false;
    const float cameraXOffsets[] = {-480.0f, -320.0f, -160.0f, 0.0f, 160.0f, 320.0f, 480.0f};
    const float cameraYOffsets[] = {-480.0f, -320.0f, -160.0f, 0.0f, 160.0f, 320.0f, 480.0f};
    const float backYawOffsets[] = {-0.16f, -0.08f, 0.0f, 0.08f, 0.16f};

    for (float cameraXOffset : cameraXOffsets)
    {
        for (float cameraYOffset : cameraYOffsets)
        {
            for (float yawOffset : backYawOffsets)
            {
                IndoorPortalVisibilityInput backInput = {};
                backInput.pMapData = &*mapData;
                backInput.pPortalGraph = &portalGraph;
                backInput.pVertices = &adjustedVertices;
                backInput.pMapDeltaData = &mapDeltaData;
                backInput.pEventRuntimeState = &eventRuntimeState;
                backInput.cameraPosition = {
                    portalCenter.x + cameraXOffset,
                    portalCenter.y + cameraYOffset,
                    portalCenter.z
                };
                const bx::Vec3 backForward = {
                    lobbyPortalCenter.x - backInput.cameraPosition.x,
                    lobbyPortalCenter.y - backInput.cameraPosition.y,
                    lobbyPortalCenter.z - backInput.cameraPosition.z
                };
                backInput.cameraForward = rotateAroundZ(backForward, yawOffset);
                backInput.cameraUp = {0.0f, 0.0f, 1.0f};
                backInput.verticalFovDegrees = 60.0f;
                backInput.aspectRatio = 16.0f / 9.0f;
                backInput.startSectorId = TargetSectorId;

                const IndoorPortalVisibilityResult backResult = buildIndoorPortalVisibility(backInput);
                const IndoorPortalVisibilityTrace *pEntryTrace =
                    findPortalTraceForFace(backResult, PortalFaceId, "accepted");
                const IndoorPortalVisibilityTrace *pLobbyTrace =
                    findPortalTraceForFace(backResult, LobbyPortalFaceId, "accepted");

                if (pEntryTrace == nullptr
                    || pEntryTrace->sourceSectorId != TargetSectorId
                    || pEntryTrace->targetSectorId != SourceSectorId
                    || pLobbyTrace == nullptr
                    || pLobbyTrace->sourceSectorId != SourceSectorId
                    || pLobbyTrace->targetSectorId != LobbySectorId)
                {
                    continue;
                }

                INFO("cameraXOffset=" << cameraXOffset);
                INFO("cameraYOffset=" << cameraYOffset);
                INFO("yawOffset=" << yawOffset);
                REQUIRE_GT(backResult.visibleSectorMask.size(), LobbySectorId);
                CHECK_EQ(backResult.visibleSectorMask[LobbySectorId], 1);
                CHECK(findPortalTraceForFace(backResult, LobbyPortalFaceId, "child_frustum_small") == nullptr);
                foundBackChain = true;
                break;
            }

            if (foundBackChain)
            {
                break;
            }
        }

        if (foundBackChain)
        {
            break;
        }
    }

    CHECK(foundBackChain);
}

TEST_CASE("indoor portal visibility keeps portals with visible vertices in front of the camera")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    IndoorFace face = {};
    face.attributes = faceAttributeBit(FaceAttribute::IsPortal);
    face.roomNumber = 1;
    face.roomBehindNumber = 0;
    face.facetType = 1;
    face.isPortal = true;
    face.vertexIndices = {
        addVertex(mapData, -400, -24, -48),
        addVertex(mapData, -400, -24, 48),
        addVertex(mapData, 50, 24, 48),
        addVertex(mapData, 50, 24, -48),
    };

    mapData.faces.push_back(std::move(face));
    const uint16_t faceId = static_cast<uint16_t>(mapData.faces.size() - 1);
    mapData.sectors[0].portalFaceIds.push_back(faceId);
    mapData.sectors[0].faceIds.push_back(faceId);
    mapData.sectors[1].portalFaceIds.push_back(faceId);
    mapData.sectors[1].faceIds.push_back(faceId);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.directionRejectedPortalCount, 0);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceWithReason(result, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->faceId, faceId);
}

TEST_CASE("cd3 diagonal arch sliver sector preserves room visibility")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "cd3.blv");

    REQUIRE_FALSE(mapBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    constexpr uint16_t SourceSectorId = 1;
    constexpr uint16_t SliverSectorId = 10;
    constexpr uint16_t TargetSectorId = 11;
    constexpr uint16_t FirstPortalFaceId = 2715;
    constexpr uint16_t SecondPortalFaceId = 2902;

    REQUIRE_GT(mapData->sectors.size(), TargetSectorId);
    REQUIRE_LT(FirstPortalFaceId, mapData->faces.size());
    REQUIRE_LT(SecondPortalFaceId, mapData->faces.size());
    CHECK_EQ(mapData->faces[FirstPortalFaceId].roomNumber, SourceSectorId);
    CHECK_EQ(mapData->faces[FirstPortalFaceId].roomBehindNumber, SliverSectorId);
    CHECK_EQ(mapData->faces[SecondPortalFaceId].roomNumber, TargetSectorId);
    CHECK_EQ(mapData->faces[SecondPortalFaceId].roomBehindNumber, SliverSectorId);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &mapData->vertices;
    input.cameraPosition = {6371.0f, 3445.0f, 240.0f};
    const bx::Vec3 portalCenter = faceCenter(*mapData, FirstPortalFaceId);
    input.cameraForward = {
        portalCenter.x - input.cameraPosition.x,
        portalCenter.y - input.cameraPosition.y,
        portalCenter.z - input.cameraPosition.z
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 16.0f / 9.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    CHECK_EQ(result.visibleSectorMask[SliverSectorId], 1);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    const IndoorPortalVisibilityTrace *pSecondPortalTrace =
        findPortalTraceForFace(result, SecondPortalFaceId, "accepted");
    REQUIRE(pSecondPortalTrace != nullptr);
    CHECK_EQ(pSecondPortalTrace->sourceSectorId, SliverSectorId);
    CHECK_EQ(pSecondPortalTrace->targetSectorId, TargetSectorId);
}

TEST_CASE("cd3 actor detection crosses diagonal sliver sector without portal backtracking")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "cd3.blv");

    REQUIRE_FALSE(mapBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    constexpr int16_t PartySectorId = 1;
    constexpr int16_t SliverSectorId = 10;
    constexpr int16_t ActorSectorId = 11;
    constexpr uint16_t PartyPortalFaceId = 2715;
    constexpr uint16_t ActorPortalFaceId = 2902;

    IndoorFaceGeometryCache geometryCache(mapData->faces.size());
    const IndoorFaceGeometryData *pPartyPortalGeometry =
        geometryCache.geometryForFace(*mapData, mapData->vertices, PartyPortalFaceId);
    const IndoorFaceGeometryData *pActorPortalGeometry =
        geometryCache.geometryForFace(*mapData, mapData->vertices, ActorPortalFaceId);
    REQUIRE(pPartyPortalGeometry != nullptr);
    REQUIRE(pActorPortalGeometry != nullptr);
    REQUIRE(!pPartyPortalGeometry->vertices.empty());
    REQUIRE(!pActorPortalGeometry->vertices.empty());

    const bx::Vec3 actorPortalCenter = faceCenter(*mapData, ActorPortalFaceId);
    const bx::Vec3 partyPortalCenter = faceCenter(*mapData, PartyPortalFaceId);
    const bx::Vec3 actorPoint = {
        actorPortalCenter.x + pActorPortalGeometry->normal.x * 128.0f,
        actorPortalCenter.y + pActorPortalGeometry->normal.y * 128.0f,
        actorPortalCenter.z + pActorPortalGeometry->normal.z * 128.0f
    };
    const bx::Vec3 partyPoint = {
        partyPortalCenter.x + pPartyPortalGeometry->normal.x * 128.0f,
        partyPortalCenter.y + pPartyPortalGeometry->normal.y * 128.0f,
        partyPortalCenter.z + pPartyPortalGeometry->normal.z * 128.0f
    };

    const IndoorPortalSectorTrace actorToPartyTrace =
        traceIndoorLineThroughPortalSectors(
            *mapData,
            mapData->vertices,
            geometryCache,
            actorPoint,
            ActorSectorId,
            partyPoint,
            PartySectorId,
            30);

    CHECK(actorToPartyTrace.reachedTargetSector);
    CHECK_EQ(actorToPartyTrace.sectorIds, std::vector<int16_t>{ActorSectorId, SliverSectorId, PartySectorId});

    const IndoorPortalSectorTrace partyToActorTrace =
        traceIndoorLineThroughPortalSectors(
            *mapData,
            mapData->vertices,
            geometryCache,
            partyPoint,
            PartySectorId,
            actorPoint,
            ActorSectorId,
            30);

    CHECK(partyToActorTrace.reachedTargetSector);
    CHECK_EQ(partyToActorTrace.sectorIds, std::vector<int16_t>{PartySectorId, SliverSectorId, ActorSectorId});
}

TEST_CASE("indoor portal line traces take an end just past a doorway as in the sector it came from")
{
    // Sector 0 below x 100, sector 1 beyond. The sector lookup gives a point a unit past a doorway the sector it came
    // from (Thronheim City's Desert Terror, 2026-11-08: its strafe left it at x 8705 of a doorway at 8704, still
    // sector 2, and no line from or to it reached the guard 72 units on in sector 4).
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);
    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    IndoorFaceGeometryCache geometryCache(mapData.faces.size());
    const auto trace = [&](const bx::Vec3 &from, int16_t fromSector, const bx::Vec3 &to, int16_t toSector)
    {
        return traceIndoorLineThroughPortalSectors(mapData, mapData.vertices, geometryCache, from, fromSector, to,
            toSector, 30).reachedTargetSector;
    };

    CHECK(trace({50.0f, 0.0f, 0.0f}, 0, {180.0f, 0.0f, 0.0f}, 1));
    // a start of sector 0 a unit past the doorway, and the same point as the end of a line from sector 1
    CHECK(trace({101.0f, 0.0f, 0.0f}, 0, {180.0f, 0.0f, 0.0f}, 1));
    CHECK(trace({180.0f, 0.0f, 0.0f}, 1, {101.0f, 0.0f, 0.0f}, 0));
    // farther past than the lookup ever takes a point (8 units): a wrong sector, no line
    CHECK_FALSE(trace({120.0f, 0.0f, 0.0f}, 0, {180.0f, 0.0f, 0.0f}, 1));
    CHECK_FALSE(trace({180.0f, 0.0f, 0.0f}, 1, {120.0f, 0.0f, 0.0f}, 0));
    // past the doorway but beside it (outside the opening): no line
    CHECK_FALSE(trace({101.0f, 60.0f, 0.0f}, 0, {180.0f, 60.0f, 0.0f}, 1));
}

TEST_CASE("indoor portal visibility does not traverse portal faces missing from sector portal lists")
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
    CHECK_EQ(result.visibleSectorMask[1], 0);
    CHECK_EQ(result.acceptedPortalCount, 0);
}

TEST_CASE("indoor portal visibility opens the whole view through a dropped portal beside the camera")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);
    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    // The camera's sector is 0 (the floor under it), but it stands 24 units past the portal, looking away from it:
    // the portal faces away and would be dropped, and sector 1, where the camera really is, would not be drawn.
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.collectPortalTraces = true;
    input.nearPortalReach = 96.0f;
    input.cameraPosition = {124.0f, 0.0f, 0.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};
    const IndoorPortalVisibilityResult past = buildIndoorPortalVisibility(input);
    CHECK_EQ(past.visibleSectorMask[1], 1);
    REQUIRE_EQ(past.frustumsBySector[1].size(), 1);
    CHECK(sphereIntersectsAnyFrustum({400.0f, 100.0f, 0.0f}, 8.0f, past.frustumsBySector[1]));

    // Beside the portal on its own side, looking along the wall: the portal is out of view but within reach.
    input.cameraPosition = {60.0f, 0.0f, 0.0f};
    input.cameraForward = {0.0f, 1.0f, 0.0f};
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 1);

    // Farther than the reach, the portal is dropped as before; and with no reach (every MM6-MM8 map) MM8's rule only.
    input.cameraPosition = {300.0f, 0.0f, 0.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};
    const IndoorPortalVisibilityResult far = buildIndoorPortalVisibility(input);
    CHECK_EQ(far.visibleSectorMask[1], 0);
    CHECK(findPortalTraceForFace(far, faceId, "portal_facing") != nullptr);
    input.cameraPosition = {124.0f, 0.0f, 0.0f};
    input.nearPortalReach = 0.0f;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 0);

    // Deeper: a second portal 10 units past the first, the camera between them looking away: sector 1 opens by MM8's
    // rule, and its portal to sector 2, edge-on behind the camera, passes on the view it is reached through.
    mapData.sectors.resize(3);
    addPortalFace(mapData, 1, 2, 110, -40, 40, -40, 40);
    input.nearPortalReach = 96.0f;
    input.cameraPosition = {104.0f, 0.0f, 0.0f};
    input.cameraForward = {-1.0f, 0.0f, 0.0f};
    const IndoorPortalVisibilityResult deeper = buildIndoorPortalVisibility(input);
    CHECK_EQ(deeper.visibleSectorMask[1], 1);
    CHECK_EQ(deeper.visibleSectorMask[2], 1);
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

TEST_CASE("indoor portal visibility limits the near portal exception to the initial node and MM8 distances")
{
    IndoorMapData mapData;
    mapData.sectors.resize(2);
    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.cameraForward = {-1.0f, 0.0f, 0.0f};
    input.cameraPosition = {91.0f, 56.0f, 0.0f};
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 1);

    input.cameraPosition.x = 90.9f;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 0);
    input.cameraPosition = {91.0f, 56.1f, 0.0f};
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 0);

    mapData.sectors.resize(3);
    addPortalFace(mapData, 1, 2, 96, -40, 40, -40, 40);
    input.cameraPosition = {92.0f, 0.0f, 0.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};
    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 0);
}

TEST_CASE("indoor portal visibility retains clipping through horizontal portals")
{
    IndoorMapData mapData;
    mapData.sectors.resize(3);
    addPortalFace(mapData, 0, 1, 100, -20, 20, -20, 20);
    addPortalFace(mapData, 1, 2, 200, 70, 90, -10, 10);
    for (IndoorVertex &vertex : mapData.vertices)
    {
        vertex = {vertex.y, vertex.z, vertex.x};
    }
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.cameraForward = {0.0f, 0.0f, 1.0f};
    input.cameraUp = {0.0f, 1.0f, 0.0f};
    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 0);
}

TEST_CASE("indoor portal visibility rejects the wrong side of an authored portal plane")
{
    IndoorMapData mapData;
    mapData.sectors.resize(2);
    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.startSectorId = 1;
    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);
    CHECK_EQ(result.visibleSectorMask[0], 0);
    CHECK(findPortalTraceForFace(result, faceId, "portal_facing") != nullptr);

    input.cameraPosition.x = 200.0f;
    input.cameraForward.x = -1.0f;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[0], 1);
}

TEST_CASE("indoor render portals need a nonzero projected screen row span")
{
    IndoorMapData mapData;
    mapData.sectors.resize(2);
    const uint16_t faceId = addPortalFace(mapData, 0, 1, 4096, -64, 64, 100, 101);
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.viewportHeight = 480;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 0);

    std::vector<IndoorVertex> openedVertices = mapData.vertices;
    const IndoorFace &face = mapData.faces[faceId];
    openedVertices[face.vertexIndices[1]].z = 500;
    openedVertices[face.vertexIndices[2]].z = 500;
    input.pVertices = &openedVertices;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 1);

    input.pVertices = &mapData.vertices;
    input.viewportHeight = 0;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[1], 1);
}

TEST_CASE("indoor portal visibility respects front and back sectors with reversed child portal winding")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);

    IndoorFace reversedPortal = {};
    reversedPortal.attributes = faceAttributeBit(FaceAttribute::IsPortal);
    reversedPortal.roomNumber = 2;
    reversedPortal.roomBehindNumber = 1;
    reversedPortal.facetType = 1;
    reversedPortal.isPortal = true;
    reversedPortal.vertexIndices = {
        addVertex(mapData, 200, -35, -35),
        addVertex(mapData, 200, 35, -35),
        addVertex(mapData, 200, 35, 35),
        addVertex(mapData, 200, -35, 35),
    };

    mapData.faces.push_back(std::move(reversedPortal));
    const uint16_t reversedPortalFaceId = static_cast<uint16_t>(mapData.faces.size() - 1);
    mapData.sectors[1].portalFaceIds.push_back(reversedPortalFaceId);
    mapData.sectors[1].faceIds.push_back(reversedPortalFaceId);
    mapData.sectors[2].portalFaceIds.push_back(reversedPortalFaceId);
    mapData.sectors[2].faceIds.push_back(reversedPortalFaceId);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 3);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 1);
}

TEST_CASE("indoor portal visibility traverses invisible portal faces")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    mapData.faces[faceId].attributes |= faceAttributeBit(FaceAttribute::Invisible);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(makeVisibilityInput(mapData));

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.acceptedPortalCount, 1);
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

TEST_CASE("indoor portal visibility does not include frustum-visible unlinked geometry sectors")
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
    CHECK_EQ(result.visibleSectorMask[1], 0);
    CHECK_EQ(result.orphanVisibleSectorCount, 0);
}

TEST_CASE("indoor portal visibility does not seed linked sectors when starting inside unlinked geometry")
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
    CHECK_EQ(result.visibleSectorMask[1], 0);
    CHECK_EQ(result.visibleSectorMask[2], 0);
}

TEST_CASE("indoor portal visibility traverses closed mechanism door portals")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    const uint16_t solidFaceId = addSolidDoorFace(mapData, 50, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        faceId,
        solidFaceId,
        static_cast<uint16_t>(EvtMechanismState::Closed)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceWithReason(result, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
}

TEST_CASE("indoor portal visibility ignores unlinked closed door geometry")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    const uint16_t solidFaceId = addSolidDoorFace(mapData, 50, -40, 40, -40, 40);

    MapDeltaDoor door = {};
    door.doorId = 23;
    door.state = static_cast<uint16_t>(EvtMechanismState::Closed);
    door.moveLength = 100;
    door.openSpeed = 100;
    door.closeSpeed = 100;
    door.faceIds.push_back(solidFaceId);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(door);

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceWithReason(result, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
}

TEST_CASE("indoor portal visibility does not reapply crossed entry door geometry to child portals")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);

    const uint16_t entryPortalFaceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    addPortalFace(mapData, 1, 2, 200, -35, 35, -35, 35);
    const uint16_t entryDoorSolidFaceId = addSolidDoorFace(mapData, 170, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        17,
        entryPortalFaceId,
        entryDoorSolidFaceId,
        static_cast<uint16_t>(EvtMechanismState::Closed)
    ));

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(mapData, &mapDeltaData);
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;
    input.pPortalGraph = &portalGraph;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 3);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    CHECK_EQ(result.visibleSectorMask[2], 1);
}

TEST_CASE("indoor portal visibility allows traversal through open mechanism doors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    const uint16_t solidFaceId = addSolidDoorFace(mapData, 50, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        faceId,
        solidFaceId,
        static_cast<uint16_t>(EvtMechanismState::Open)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;
    std::vector<IndoorVertex> openVertices = mapData.vertices;
    translateFaceVertices(openVertices, mapData.faces[solidFaceId], 0, 200, 0);
    input.pVertices = &openVertices;
    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState openDoorState = {};
    openDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    eventRuntimeState->mechanisms[1] = openDoorState;
    input.pEventRuntimeState = &eventRuntimeState;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceWithReason(result, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
}

TEST_CASE("indoor portal visibility traverses occluding initial-state door geometry")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    const uint16_t solidFaceId = addSolidDoorFace(mapData, 50, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        faceId,
        solidFaceId,
        static_cast<uint16_t>(EvtMechanismState::Open)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceWithReason(result, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
}

TEST_CASE("indoor portal visibility allows traversal through moving mechanism doors")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(2);

    const uint16_t faceId = addPortalFace(mapData, 0, 1, 100, -40, 40, -40, 40);
    const uint16_t solidFaceId = addSolidDoorFace(mapData, 50, -40, 40, -40, 40);

    MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back(makeDoorBlockingFace(
        1,
        faceId,
        solidFaceId,
        static_cast<uint16_t>(EvtMechanismState::Opening)
    ));

    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &mapDeltaData;
    std::vector<IndoorVertex> openingVertices = mapData.vertices;
    translateFaceVertices(openingVertices, mapData.faces[solidFaceId], 0, 200, 0);
    input.pVertices = &openingVertices;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_EQ(result.visibleSectorMask.size(), 2);
    CHECK_EQ(result.visibleSectorMask[0], 1);
    CHECK_EQ(result.visibleSectorMask[1], 1);
}

TEST_CASE("d18 naga vault portal 318 traversal is independent of sliding door state")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm8" / "maps" / "d18.blv");
    const std::vector<uint8_t> deltaBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm8" / "_legacy" / "map_delta" / "d18.dlv");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(deltaBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    const MapDeltaDataLoader mapDeltaDataLoader = {};
    std::optional<MapDeltaData> mapDeltaData = mapDeltaDataLoader.loadIndoorFromBytes(deltaBytes, *mapData);
    REQUIRE(mapDeltaData);

    constexpr uint16_t Room3SectorId = 3;
    constexpr uint16_t NagaRoomSectorId = 4;
    constexpr uint16_t NagaPortalFaceId = 318;
    constexpr uint32_t SlidingDoorId = 5;

    REQUIRE_LT(NagaPortalFaceId, mapData->faces.size());
    CHECK_EQ(mapData->faces[NagaPortalFaceId].roomNumber, NagaRoomSectorId);
    CHECK_EQ(mapData->faces[NagaPortalFaceId].roomBehindNumber, Room3SectorId);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &*mapDeltaData);
    const MapDeltaDoor *pSlidingDoor = findDoorById(*mapDeltaData, SlidingDoorId);
    REQUIRE(pSlidingDoor != nullptr);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &mapData->vertices;
    input.pMapDeltaData = &*mapDeltaData;
    input.cameraPosition = {416.0f, 0.0f, 0.0f};
    input.cameraForward = {0.0f, -1.0f, 0.0f};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = Room3SectorId;

    const IndoorPortalVisibilityResult closedResult = buildIndoorPortalVisibility(input);
    REQUIRE_GT(closedResult.visibleSectorMask.size(), NagaRoomSectorId);
    CHECK_EQ(closedResult.visibleSectorMask[NagaRoomSectorId], 1);
    const IndoorPortalVisibilityTrace *pClosedTrace =
        findPortalTraceForFace(closedResult, NagaPortalFaceId, "accepted");
    REQUIRE(pClosedTrace != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};

    RuntimeMechanismState halfOpenDoorState = {};
    halfOpenDoorState.state = static_cast<uint16_t>(EvtMechanismState::Opening);
    halfOpenDoorState.currentDistance = static_cast<float>(pSlidingDoor->moveLength) * 0.5f;
    halfOpenDoorState.isMoving = true;
    eventRuntimeState->mechanisms[SlidingDoorId] = halfOpenDoorState;
    input.pEventRuntimeState = &eventRuntimeState;
    const std::vector<IndoorVertex> halfOpenVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &*mapDeltaData, &*eventRuntimeState);
    input.pVertices = &halfOpenVertices;

    const IndoorPortalVisibilityResult halfOpenResult = buildIndoorPortalVisibility(input);
    REQUIRE_GT(halfOpenResult.visibleSectorMask.size(), NagaRoomSectorId);
    CHECK_EQ(halfOpenResult.visibleSectorMask[NagaRoomSectorId], 1);
    const IndoorPortalVisibilityTrace *pHalfOpenTrace =
        findPortalTraceForFace(halfOpenResult, NagaPortalFaceId, "accepted");
    REQUIRE(pHalfOpenTrace != nullptr);

    RuntimeMechanismState openDoorState = {};
    openDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    openDoorState.currentDistance = 0.0f;
    openDoorState.isMoving = false;
    eventRuntimeState->mechanisms[SlidingDoorId] = openDoorState;
    const std::vector<IndoorVertex> openVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &*mapDeltaData, &*eventRuntimeState);
    input.pVertices = &openVertices;

    const IndoorPortalVisibilityResult openResult = buildIndoorPortalVisibility(input);
    REQUIRE_GT(openResult.visibleSectorMask.size(), NagaRoomSectorId);
    CHECK_EQ(openResult.visibleSectorMask[NagaRoomSectorId], 1);
    const IndoorPortalVisibilityTrace *pOpenTrace =
        findPortalTraceForFace(openResult, NagaPortalFaceId, "accepted");
    REQUIRE(pOpenTrace != nullptr);
    CHECK_EQ(pOpenTrace->targetSectorId, NagaRoomSectorId);

    input.cameraPosition = {560.0f, 0.0f, 0.0f};
    const IndoorPortalVisibilityResult openFromRightEdgeResult = buildIndoorPortalVisibility(input);
    REQUIRE_GT(openFromRightEdgeResult.visibleSectorMask.size(), NagaRoomSectorId);
    CHECK_EQ(openFromRightEdgeResult.visibleSectorMask[NagaRoomSectorId], 1);
    const IndoorPortalVisibilityTrace *pOpenFromRightEdgeTrace =
        findPortalTraceForFace(openFromRightEdgeResult, NagaPortalFaceId, "accepted");
    REQUIRE(pOpenFromRightEdgeTrace != nullptr);
    CHECK_EQ(pOpenFromRightEdgeTrace->targetSectorId, NagaRoomSectorId);
}

TEST_CASE("6d02 portal 3201 is not blocked by edge-adjacent closed door 2")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d02.blv");
    const std::vector<uint8_t> deltaBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "_legacy" / "map_delta" / "6d02.dlv");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(deltaBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    const MapDeltaDataLoader mapDeltaDataLoader = {};
    std::optional<MapDeltaData> mapDeltaData = mapDeltaDataLoader.loadIndoorFromBytes(deltaBytes, *mapData);
    REQUIRE(mapDeltaData);

    constexpr uint16_t DoorFaceId = 2823;
    constexpr uint16_t PortalFaceId = 3201;
    constexpr uint32_t EdgeAdjacentDoorId = 2;
    constexpr uint32_t OpenPortalDoorId = 7;

    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const MapDeltaDoor *pEdgeAdjacentDoor = findDoorContainingFace(*mapDeltaData, DoorFaceId);
    REQUIRE(pEdgeAdjacentDoor != nullptr);
    CHECK_EQ(pEdgeAdjacentDoor->doorId, EdgeAdjacentDoorId);
    const MapDeltaDoor *pOpenPortalDoor = findDoorById(*mapDeltaData, OpenPortalDoorId);
    REQUIRE(pOpenPortalDoor != nullptr);

    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_NE(portalFace.roomNumber, portalFace.roomBehindNumber);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &*mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState openDoorState = {};
    openDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    openDoorState.currentDistance = 0.0f;
    openDoorState.isMoving = false;
    eventRuntimeState->mechanisms[pOpenPortalDoor->doorId] = openDoorState;

    RuntimeMechanismState closedDoorState = {};
    closedDoorState.state = static_cast<uint16_t>(EvtMechanismState::Closed);
    closedDoorState.currentDistance = static_cast<float>(pEdgeAdjacentDoor->moveLength);
    closedDoorState.isMoving = false;
    eventRuntimeState->mechanisms[pEdgeAdjacentDoor->doorId] = closedDoorState;

    const std::vector<IndoorVertex> adjustedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &*mapDeltaData, &*eventRuntimeState);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &adjustedVertices;
    input.pMapDeltaData = &*mapDeltaData;
    input.pEventRuntimeState = &eventRuntimeState;
    const bx::Vec3 portalCenter = faceCenter(*mapData, PortalFaceId);
    input.cameraPosition = {16000.0f, -16000.0f, portalCenter.z};
    input.cameraForward = {
        portalCenter.x - input.cameraPosition.x,
        portalCenter.y - input.cameraPosition.y,
        portalCenter.z - input.cameraPosition.z
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = static_cast<int16_t>(portalFace.roomNumber);

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), portalFace.roomBehindNumber);
    CHECK_EQ(result.visibleSectorMask[portalFace.roomBehindNumber], 1);
    const IndoorPortalVisibilityTrace *pOpenTrace =
        findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pOpenTrace != nullptr);
    CHECK_EQ(pOpenTrace->targetSectorId, portalFace.roomBehindNumber);
}

TEST_CASE("6d02 portal 2665 becomes visible when its authored door aperture opens")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d02.blv");

    REQUIRE_FALSE(mapBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    constexpr uint16_t PortalFaceId = 2665;
    constexpr uint16_t SourceSectorId = 48;
    constexpr uint16_t TargetSectorId = 51;

    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, SourceSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, TargetSectorId);
    CHECK_GE(mapData->sectors[SourceSectorId].maxX, mapData->sectors[TargetSectorId].minX);
    CHECK_LE(mapData->sectors[SourceSectorId].minY, mapData->sectors[TargetSectorId].maxY);
    CHECK_GE(mapData->sectors[SourceSectorId].maxY, mapData->sectors[TargetSectorId].minY);

    const std::string sceneText = readTextFile(sourceRoot / "assets_dev" / "worlds" / "mm6"
        / "maps" / "6d02.scene.yml");
    std::string error;
    const std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(sceneText, error);
    REQUIRE_MESSAGE(scene, error);
    MapDeltaData delta;
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*scene, *mapData, delta, error), error);
    std::optional<EventRuntimeState> state = EventRuntimeState{};
    EventRuntime{}.initializeMapRuntimeState(delta, *state);
    const MapDeltaDoor *pDoor = findDoorById(delta, 3);
    REQUIRE(pDoor != nullptr);
    std::vector<IndoorVertex> vertices = buildIndoorMechanismAdjustedVertices(*mapData, &delta, &*state);
    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &delta);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &vertices;
    input.cameraPosition = {16512.0f, -16200.0f, 352.0f};
    input.cameraForward = {1.0f, 0.0f, 0.0f};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult closed = buildIndoorPortalVisibility(input);
    CHECK_EQ(closed.visibleSectorMask[TargetSectorId], 0);
    CHECK(findPortalTraceForFace(closed, PortalFaceId, "clipped_portal") != nullptr);

    state->mechanisms[pDoor->doorId].currentDistance = pDoor->moveLength;
    vertices = buildIndoorMechanismAdjustedVertices(*mapData, &delta, &*state);
    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    CHECK(findPortalTraceForFace(result, PortalFaceId, "clipped_portal") == nullptr);
    CHECK(findPortalTraceForFace(result, PortalFaceId, "clipped_shared_boundary") == nullptr);
    const IndoorPortalVisibilityTrace *pAcceptedTrace =
        findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);
}

TEST_CASE("6d02 portal 3392 from sector 47 is not blocked by adjacent state-zero door 2")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d02.blv");
    const std::vector<uint8_t> deltaBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "_legacy" / "map_delta" / "6d02.dlv");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(deltaBytes.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    const MapDeltaDataLoader mapDeltaDataLoader = {};
    std::optional<MapDeltaData> mapDeltaData = mapDeltaDataLoader.loadIndoorFromBytes(deltaBytes, *mapData);
    REQUIRE(mapDeltaData);

    constexpr uint16_t SourceSectorId = 47;
    constexpr uint16_t TargetSectorId = 49;
    constexpr uint16_t PortalFaceId = 3392;
    constexpr uint32_t DoorId = 2;

    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, SourceSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, TargetSectorId);

    const MapDeltaDoor *pDoor = findDoorById(*mapDeltaData, DoorId);
    REQUIRE(pDoor != nullptr);
    CHECK_EQ(pDoor->state, static_cast<uint16_t>(EvtMechanismState::Open));
    CHECK(std::find(pDoor->sectorIds.begin(), pDoor->sectorIds.end(), SourceSectorId) == pDoor->sectorIds.end());
    REQUIRE(std::find(pDoor->sectorIds.begin(), pDoor->sectorIds.end(), TargetSectorId) != pDoor->sectorIds.end());

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &*mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &mapData->vertices;
    input.pMapDeltaData = &*mapDeltaData;
    const bx::Vec3 cameraPosition = sectorBoundsCenter(*mapData, SourceSectorId);
    const bx::Vec3 portalCenter = faceCenter(*mapData, PortalFaceId);
    input.cameraPosition = cameraPosition;
    input.cameraForward = {
        portalCenter.x - cameraPosition.x,
        portalCenter.y - cameraPosition.y,
        portalCenter.z - cameraPosition.z
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);
}

TEST_CASE("6d01 portal 116 is not blocked by unlinked closed door bounds")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d01.blv");
    const std::string sceneText =
        readTextFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d01.scene.yml");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(sceneText.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    std::string sceneError;
    const IndoorSceneYmlLoader sceneLoader = {};
    std::optional<IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData, sceneError);

    constexpr uint16_t PortalFaceId = 116;
    constexpr uint32_t SurroundingDoorId = 32;
    constexpr uint16_t SourceSectorId = 4;
    constexpr uint16_t TargetSectorId = 3;

    MapDeltaData mapDeltaData = {};
    mapDeltaData.faceAttributes.resize(mapData->faces.size());

    for (size_t faceIndex = 0; faceIndex < mapData->faces.size(); ++faceIndex)
    {
        mapDeltaData.faceAttributes[faceIndex] = mapData->faces[faceIndex].attributes;
    }

    for (const IndoorSceneDoor &sceneDoor : sceneData->initialState.doors)
    {
        mapDeltaData.doors.push_back(sceneDoor.door);
    }

    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, SourceSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, TargetSectorId);

    const MapDeltaDoor *pSurroundingDoor = findDoorById(mapDeltaData, SurroundingDoorId);
    REQUIRE(pSurroundingDoor != nullptr);
    REQUIRE(std::find(pSurroundingDoor->faceIds.begin(), pSurroundingDoor->faceIds.end(), PortalFaceId)
            == pSurroundingDoor->faceIds.end());

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState closedDoorState = {};
    closedDoorState.state = static_cast<uint16_t>(EvtMechanismState::Closed);
    closedDoorState.currentDistance = static_cast<float>(pSurroundingDoor->moveLength);
    closedDoorState.isMoving = false;
    eventRuntimeState->mechanisms[SurroundingDoorId] = closedDoorState;

    const std::vector<IndoorVertex> adjustedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &mapDeltaData, &*eventRuntimeState);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &adjustedVertices;
    input.pMapDeltaData = &mapDeltaData;
    input.pEventRuntimeState = &eventRuntimeState;
    input.cameraPosition = {-192.0f, 3900.0f, 128.0f};
    input.cameraForward = {0.0f, 1.0f, 0.0f};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace =
        findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);
}

TEST_CASE("6d01 room 7 chest portal 1941 is visible after opening its chest door")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d01.blv");
    const std::string sceneText =
        readTextFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "6d01.scene.yml");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(sceneText.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    std::string sceneError;
    const IndoorSceneYmlLoader sceneLoader = {};
    std::optional<IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData, sceneError);

    MapDeltaData mapDeltaData = {};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*sceneData, *mapData, mapDeltaData, sceneError), sceneError);

    constexpr uint16_t SourceSectorId = 7;
    constexpr uint16_t TargetSectorId = 13;
    constexpr uint16_t PortalFaceId = 1941;
    constexpr uint32_t OpenedDoorId = 9;
    constexpr uint32_t AdjacentDoorId = 8;

    REQUIRE_LT(PortalFaceId, mapData->faces.size());
    const IndoorFace &portalFace = mapData->faces[PortalFaceId];
    REQUIRE_EQ(portalFace.roomNumber, TargetSectorId);
    REQUIRE_EQ(portalFace.roomBehindNumber, SourceSectorId);

    const MapDeltaDoor *pOpenedDoor = findDoorById(mapDeltaData, OpenedDoorId);
    REQUIRE(pOpenedDoor != nullptr);
    const MapDeltaDoor *pAdjacentDoor = findDoorById(mapDeltaData, AdjacentDoorId);
    REQUIRE(pAdjacentDoor != nullptr);
    REQUIRE_GT(pOpenedDoor->sectorIds.size(), 2);
    REQUIRE_GT(pAdjacentDoor->sectorIds.size(), 2);

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, PortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState openedDoorState = {};
    openedDoorState.state = static_cast<uint16_t>(EvtMechanismState::Closed);
    openedDoorState.currentDistance = static_cast<float>(pOpenedDoor->moveLength);
    openedDoorState.isMoving = false;
    eventRuntimeState->mechanisms[OpenedDoorId] = openedDoorState;

    RuntimeMechanismState adjacentDoorState = {};
    adjacentDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    adjacentDoorState.currentDistance = 0.0f;
    adjacentDoorState.isMoving = false;
    eventRuntimeState->mechanisms[AdjacentDoorId] = adjacentDoorState;

    const std::vector<IndoorVertex> adjustedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &mapDeltaData, &*eventRuntimeState);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &adjustedVertices;
    input.pMapDeltaData = &mapDeltaData;
    input.pEventRuntimeState = &eventRuntimeState;
    const bx::Vec3 cameraPosition = sectorBoundsCenter(*mapData, SourceSectorId);
    const bx::Vec3 portalCenter = faceCenter(*mapData, PortalFaceId);
    input.cameraPosition = cameraPosition;
    input.cameraForward = {
        portalCenter.x - cameraPosition.x,
        portalCenter.y - cameraPosition.y,
        portalCenter.z - cameraPosition.z
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = SourceSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), TargetSectorId);
    CHECK_EQ(result.visibleSectorMask[TargetSectorId], 1);
    const IndoorPortalVisibilityTrace *pAcceptedTrace = findPortalTraceForFace(result, PortalFaceId, "accepted");
    REQUIRE(pAcceptedTrace != nullptr);
    CHECK_EQ(pAcceptedTrace->targetSectorId, TargetSectorId);

}

TEST_CASE("Goblinwatch entrance discovery uses closed and moving door apertures")
{
    const std::filesystem::path mapRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev" / "worlds" / "mm6" / "maps";
    std::optional<IndoorMapData> map = IndoorMapDataLoader{}.loadFromBytes(
        readBinaryFile(mapRoot / "6d01.blv"));
    REQUIRE(map);
    std::string error;
    const std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(
        readTextFile(mapRoot / "6d01.scene.yml"), error);
    REQUIRE_MESSAGE(scene, error);
    MapDeltaData delta;
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*scene, *map, delta, error), error);
    std::optional<EventRuntimeState> state = EventRuntimeState{};
    EventRuntime{}.initializeMapRuntimeState(delta, *state);
    std::vector<IndoorVertex> vertices = buildIndoorMechanismAdjustedVertices(*map, &delta, &*state);
    const IndoorPortalGraph graph = buildIndoorPortalGraph(*map, &delta);
    IndoorPortalVisibilityInput input = makeVisibilityInput(*map);
    input.pVertices = &vertices;
    input.pPortalGraph = &graph;
    input.pMapDeltaData = &delta;
    input.pEventRuntimeState = &state;
    input.cameraPosition = {576.0f, 6912.0f, 352.0f};
    const float yaw = 4.672f;
    const float pitch = -0.250507f;
    input.cameraForward = {std::cos(yaw) * std::cos(pitch), std::sin(yaw) * std::cos(pitch), std::sin(pitch)};
    input.aspectRatio = 16.0f / 9.0f;
    input.startSectorId = 1;

    for (int height : {480, 900})
    {
        input.viewportHeight = height;
        const IndoorPortalVisibilityResult closed = buildIndoorPortalVisibility(input);
        REQUIRE_GT(closed.visibleSectorMask.size(), 53);
        CHECK_EQ(closed.visibleSectorMask[1], 1);
        for (int sectorId : {3, 4, 6, 21, 48, 53})
        {
            INFO("height=" << height << " sector=" << sectorId);
            CHECK_EQ(closed.visibleSectorMask[sectorId], 0);
        }
    }

    const MapDeltaDoor *pDoor = findDoorById(delta, 1);
    REQUIRE(pDoor != nullptr);
    state->mechanisms[pDoor->doorId].currentDistance = pDoor->moveLength;
    vertices = buildIndoorMechanismAdjustedVertices(*map, &delta, &*state);
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[3], 1);

    state->mechanisms[pDoor->doorId].currentDistance = 0.0f;
    vertices = buildIndoorMechanismAdjustedVertices(*map, &delta, &*state);
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask[3], 0);
}

TEST_CASE("hive start sector 76 portal traversal ignores entrance door endpoint naming")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> mapBytes =
        readBinaryFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "hive.blv");
    const std::string sceneText =
        readTextFile(sourceRoot / "assets_dev" / "worlds" / "mm6" / "maps" / "hive.scene.yml");

    REQUIRE_FALSE(mapBytes.empty());
    REQUIRE_FALSE(sceneText.empty());

    const IndoorMapDataLoader mapDataLoader = {};
    std::optional<IndoorMapData> mapData = mapDataLoader.loadFromBytes(mapBytes);
    REQUIRE(mapData);

    std::string sceneError;
    const IndoorSceneYmlLoader sceneLoader = {};
    std::optional<IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData, sceneError);

    MapDeltaData mapDeltaData = {};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*sceneData, *mapData, mapDeltaData, sceneError), sceneError);

    constexpr uint16_t StartSectorId = 76;
    constexpr uint16_t EntranceSectorId = 1;
    constexpr uint16_t EntrancePortalFaceId = 3012;
    constexpr uint32_t EntranceDoorId = 1;

    REQUIRE_GT(mapData->sectors.size(), StartSectorId);
    REQUIRE_LT(EntrancePortalFaceId, mapData->faces.size());
    const IndoorFace &entrancePortalFace = mapData->faces[EntrancePortalFaceId];
    CHECK_EQ(entrancePortalFace.roomNumber, StartSectorId);
    CHECK_EQ(entrancePortalFace.roomBehindNumber, EntranceSectorId);

    const MapDeltaDoor *pEntranceDoor = findDoorById(mapDeltaData, EntranceDoorId);
    REQUIRE(pEntranceDoor != nullptr);
    CHECK_EQ(pEntranceDoor->state, static_cast<uint16_t>(EvtMechanismState::Open));
    REQUIRE(
        std::find(pEntranceDoor->faceIds.begin(), pEntranceDoor->faceIds.end(), EntrancePortalFaceId)
        != pEntranceDoor->faceIds.end());

    const IndoorPortalGraph portalGraph = buildIndoorPortalGraph(*mapData, &mapDeltaData);
    const IndoorPortalLink *pPortalLink = findIndoorPortalLinkByFaceId(portalGraph, EntrancePortalFaceId);
    REQUIRE(pPortalLink != nullptr);

    std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState{};
    RuntimeMechanismState initialEntranceDoorState = {};
    initialEntranceDoorState.state = static_cast<uint16_t>(EvtMechanismState::Open);
    initialEntranceDoorState.currentDistance = 0.0f;
    initialEntranceDoorState.isMoving = false;
    eventRuntimeState->mechanisms[EntranceDoorId] = initialEntranceDoorState;

    const std::vector<IndoorVertex> adjustedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &mapDeltaData, &*eventRuntimeState);

    const bx::Vec3 cameraPosition = sectorBoundsCenter(*mapData, StartSectorId);
    const bx::Vec3 portalCenter = faceCenter(*mapData, EntrancePortalFaceId);

    IndoorPortalVisibilityInput input = {};
    input.pMapData = &*mapData;
    input.pPortalGraph = &portalGraph;
    input.pVertices = &adjustedVertices;
    input.pMapDeltaData = &mapDeltaData;
    input.pEventRuntimeState = &eventRuntimeState;
    input.cameraPosition = cameraPosition;
    input.cameraForward = {
        portalCenter.x - cameraPosition.x,
        portalCenter.y - cameraPosition.y,
        portalCenter.z - cameraPosition.z
    };
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = 1.0f;
    input.startSectorId = StartSectorId;

    const IndoorPortalVisibilityResult result = buildIndoorPortalVisibility(input);

    REQUIRE_GT(result.visibleSectorMask.size(), StartSectorId);
    REQUIRE_GT(result.visibleSectorMask.size(), EntranceSectorId);
    CHECK_EQ(result.visibleSectorMask[StartSectorId], 1);
    CHECK_EQ(result.visibleSectorMask[EntranceSectorId], 1);
    const IndoorPortalVisibilityTrace *pInitialTrace =
        findPortalTraceForFace(result, EntrancePortalFaceId, "accepted");
    REQUIRE(pInitialTrace != nullptr);
    REQUIRE_EQ(pInitialTrace->sourceSectorId, StartSectorId);
    REQUIRE_EQ(pInitialTrace->targetSectorId, EntranceSectorId);

    RuntimeMechanismState openedEntranceDoorState = {};
    openedEntranceDoorState.state = static_cast<uint16_t>(EvtMechanismState::Closed);
    openedEntranceDoorState.currentDistance = static_cast<float>(pEntranceDoor->moveLength);
    openedEntranceDoorState.isMoving = false;
    eventRuntimeState->mechanisms[EntranceDoorId] = openedEntranceDoorState;
    const std::vector<IndoorVertex> openedVertices =
        buildIndoorMechanismAdjustedVertices(*mapData, &mapDeltaData, &*eventRuntimeState);
    input.pVertices = &openedVertices;

    const IndoorPortalVisibilityResult openedResult = buildIndoorPortalVisibility(input);

    REQUIRE_GT(openedResult.visibleSectorMask.size(), EntranceSectorId);
    CHECK_EQ(openedResult.visibleSectorMask[EntranceSectorId], 1);
    const IndoorPortalVisibilityTrace *pOpenedTrace =
        findPortalTraceForFace(openedResult, EntrancePortalFaceId, "accepted");
    REQUIRE(pOpenedTrace != nullptr);
    REQUIRE_EQ(pOpenedTrace->sourceSectorId, StartSectorId);
    REQUIRE_EQ(pOpenedTrace->targetSectorId, EntranceSectorId);
}

TEST_CASE("indoor discovery portal traversal is independent of opaque door coverage")
{
    IndoorMapData mapData = {};
    mapData.sectors.resize(3);
    const uint16_t portalId = addPortalFace(mapData, 0, 1, 200, -40, 40, -40, 40);
    addPortalFace(mapData, 1, 2, 400, -40, 40, -40, 40);
    const uint16_t doorFaceId = addSolidDoorFace(mapData, 100, -40, 40, -40, 40);
    MapDeltaData delta = {};
    delta.doors.push_back(makeDoorBlockingFace(1, portalId, doorFaceId, 0));
    IndoorPortalVisibilityInput input = makeVisibilityInput(mapData);
    input.pMapDeltaData = &delta;

    // MM8 uses the ordinary portal render traversal for discovery, without subtracting opaque doors.
    for (uint16_t state = 0; state < 4; ++state)
    {
        CAPTURE(state);
        delta.doors.front().state = state;
        CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask, std::vector<uint8_t>{1, 1, 1});
    }

    std::vector<IndoorVertex> movedVertices = mapData.vertices;
    translateFaceVertices(movedVertices, mapData.faces[doorFaceId], 0, 200, 0);
    input.pVertices = &movedVertices;
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask, std::vector<uint8_t>{1, 1, 1});

    input.cameraForward = {-1.0f, 0.0f, 0.0f};
    CHECK_EQ(buildIndoorPortalVisibility(input).visibleSectorMask, std::vector<uint8_t>{1, 0, 0});
}
