#include "doctest/doctest.h"

#include "editor/document/Mm9DatLevelMetadata.h"
#include "game/mm9/Mm9DatPhysicsQuery.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace
{
OpenYAMM::Game::Mm9DatVec3 vec3(float x, float y, float z)
{
    return {x, y, z};
}

void checkVec3Approx(
    const OpenYAMM::Game::Mm9DatVec3 &actual,
    const OpenYAMM::Game::Mm9DatVec3 &expected)
{
    CHECK(actual.x == doctest::Approx(expected.x));
    CHECK(actual.y == doctest::Approx(expected.y));
    CHECK(actual.z == doctest::Approx(expected.z));
}

OpenYAMM::Game::Mm9DatVec3 add(
    const OpenYAMM::Game::Mm9DatVec3 &left,
    const OpenYAMM::Game::Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

OpenYAMM::Game::Mm9DatVec3 subtract(
    const OpenYAMM::Game::Mm9DatVec3 &left,
    const OpenYAMM::Game::Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

OpenYAMM::Game::Mm9DatVec3 multiply(const OpenYAMM::Game::Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

float dot(const OpenYAMM::Game::Mm9DatVec3 &left, const OpenYAMM::Game::Mm9DatVec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float length(const OpenYAMM::Game::Mm9DatVec3 &value)
{
    return std::sqrt(dot(value, value));
}

OpenYAMM::Game::Mm9DatVec3 queryTriangleCenter(const OpenYAMM::Game::Mm9DatPhysicsQueryTriangle &triangle)
{
    return {
        (triangle.vertex0.x + triangle.vertex1.x + triangle.vertex2.x) / 3.0f,
        (triangle.vertex0.y + triangle.vertex1.y + triangle.vertex2.y) / 3.0f,
        (triangle.vertex0.z + triangle.vertex1.z + triangle.vertex2.z) / 3.0f,
    };
}

OpenYAMM::Game::Mm9DatPickRay centerRayForQueryTriangle(
    const OpenYAMM::Game::Mm9DatPhysicsQueryTriangle &triangle,
    float offset)
{
    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = add(queryTriangleCenter(triangle), multiply(triangle.normal, offset));
    ray.direction = multiply(triangle.normal, -1.0f);
    return ray;
}

OpenYAMM::Game::Mm9DatRenderTriangle renderTriangle(
    size_t sourceModelIndex,
    size_t sourcePolyIndex,
    size_t sourceSurfaceIndex,
    float z,
    const std::string &sourceModelName,
    uint32_t surfaceFlags,
    uint16_t textureFlags)
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = sourceModelIndex;
    triangle.sourcePolyIndex = sourcePolyIndex;
    triangle.sourceSurfaceIndex = sourceSurfaceIndex;
    triangle.sourceTextureIndex = sourceSurfaceIndex + 10;
    triangle.sourceModelName = sourceModelName;
    triangle.sourceTexture = sourceModelName + "_texture";
    triangle.surfaceFlags = surfaceFlags;
    triangle.textureFlags = textureFlags;
    triangle.vertices[0].x = 0.0f;
    triangle.vertices[0].y = 0.0f;
    triangle.vertices[0].z = z;
    triangle.vertices[1].x = 1.0f;
    triangle.vertices[1].y = 0.0f;
    triangle.vertices[1].z = z;
    triangle.vertices[2].x = 0.0f;
    triangle.vertices[2].y = 1.0f;
    triangle.vertices[2].z = z;
    return triangle;
}

OpenYAMM::Game::Mm9DatRenderFilterEntry filterEntry(size_t triangleIndex, uint32_t renderFlags)
{
    OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
    entry.triangleIndex = triangleIndex;
    entry.sourceModelIndex = triangleIndex;
    entry.sourcePolyIndex = triangleIndex + 100;
    entry.sourceSurfaceIndex = triangleIndex + 200;
    entry.flags = renderFlags;
    return entry;
}

OpenYAMM::Game::Mm9DatPhysicsQueryView syntheticQueryView()
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(
        renderTriangle(
            0,
            11,
            21,
            0.0f,
            "VisibleModel",
            OpenYAMM::Game::Mm9DatSurfaceFlagSolid,
            0x0012u));
    mesh.triangles.push_back(
        renderTriangle(
            1,
            12,
            22,
            1.0f,
            "PhysicsBSP",
            OpenYAMM::Game::Mm9DatSurfaceFlagInvisible | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker,
            0x0034u));
    mesh.triangles.push_back(
        renderTriangle(
            2,
            13,
            23,
            0.5f,
            "TriggerVolume",
            OpenYAMM::Game::Mm9DatSurfaceFlagInvisible | OpenYAMM::Game::Mm9DatSurfaceFlagNotAStep,
            0x0056u));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    filters.entries.push_back(filterEntry(0, OpenYAMM::Game::Mm9DatRenderFilterVisual));
    filters.entries.push_back(
        filterEntry(
            1,
            OpenYAMM::Game::Mm9DatRenderFilterPhysics | OpenYAMM::Game::Mm9DatRenderFilterHelper
                | OpenYAMM::Game::Mm9DatRenderFilterInvisible));
    filters.entries.push_back(
        filterEntry(
            2,
            OpenYAMM::Game::Mm9DatRenderFilterTrigger | OpenYAMM::Game::Mm9DatRenderFilterHelper
                | OpenYAMM::Game::Mm9DatRenderFilterInvisible));

    return OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);
}

std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

std::string readTextFile(const std::filesystem::path &path)
{
    std::ifstream input(path);
    REQUIRE(input.good());
    return std::string((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
}

OpenYAMM::Editor::EditorMm9DatLevelMetadata loadLevelMetadata(const std::string &mapId)
{
    const std::filesystem::path levelPath =
        sourceRoot() / "assets_dev/worlds/mm9/maps" / (mapId + ".level.yml");
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(readTextFile(levelPath), errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());
    return *metadata;
}

OpenYAMM::Editor::EditorMm9DatWorldSidecar loadDatWorldSidecar(const std::string &mapId)
{
    const std::filesystem::path sidecarPath =
        sourceRoot() / "assets_dev/worlds/mm9/maps" / (mapId + ".dat_world.yml");
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> sidecar =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(readTextFile(sidecarPath), errorMessage);
    REQUIRE_MESSAGE(sidecar.has_value(), errorMessage.c_str());
    return *sidecar;
}

OpenYAMM::Game::Mm9DatWorld loadSourceDatWorld(const std::string &mapId)
{
    const OpenYAMM::Editor::EditorMm9DatLevelMetadata metadata = loadLevelMetadata(mapId);
    const std::filesystem::path levelPath =
        sourceRoot() / "assets_dev/worlds/mm9/maps" / (mapId + ".level.yml");
    const std::filesystem::path datPath =
        OpenYAMM::Editor::resolveMm9DatLevelRelativePath(levelPath, metadata.source.dat);
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DatWorld> world =
        OpenYAMM::Game::loadMm9DatWorld(datPath, errorMessage);
    REQUIRE_MESSAGE(world.has_value(), errorMessage.c_str());
    return *world;
}

std::vector<OpenYAMM::Game::Mm9DatModelRenderRole> modelRolesFromSidecar(
    const OpenYAMM::Editor::EditorMm9DatWorldSidecar &sidecar)
{
    std::vector<OpenYAMM::Game::Mm9DatModelRenderRole> roles;
    roles.reserve(sidecar.worldModels.size());

    for (const OpenYAMM::Editor::EditorMm9DatWorldModelSummary &model : sidecar.worldModels)
    {
        OpenYAMM::Game::Mm9DatModelRenderRole role = {};
        role.sourceModelIndex = model.sourceModelIndex;
        role.visible = model.roles.visible;
        role.terrain = model.roles.terrain;
        role.physicsBsp = model.roles.physicsBsp;
        role.visBsp = model.roles.visBsp;
        role.sky = model.roles.sky;
        role.water = model.roles.water;
        role.triggerOrVolume = model.roles.triggerOrVolume;
        role.movable = model.roles.movable;
        roles.push_back(role);
    }

    return roles;
}
}

TEST_CASE("MM9 DAT physics query view preserves source ids and channel stats")
{
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view = syntheticQueryView();

    REQUIRE(view.triangles.size() == 3);
    CHECK(view.stats.totalTriangles == 3);
    CHECK(view.stats.visibleTriangles == 1);
    CHECK(view.stats.physicsTriangles == 1);
    CHECK(view.stats.triggerTriangles == 1);
    CHECK(view.stats.helperTriangles == 2);
    CHECK(view.stats.sourceModelCount == 3);
    CHECK(view.stats.hasPhysicsGeometry);
    CHECK_FALSE(view.stats.hasVisibilityGeometry);

    const OpenYAMM::Game::Mm9DatPhysicsSourceRef &source = view.triangles[1].source;
    CHECK(source.queryTriangleIndex == 1);
    CHECK(source.renderTriangleIndex == 1);
    CHECK(source.sourceModelIndex == 1);
    CHECK(source.sourceModelName == "PhysicsBSP");
    CHECK(source.sourcePolyIndex == 12);
    CHECK(source.sourceSurfaceIndex == 22);
    CHECK(source.sourceTextureIndex == 32);
    CHECK(source.sourceTexture == "PhysicsBSP_texture");
    CHECK(source.surfaceFlags == (
        OpenYAMM::Game::Mm9DatSurfaceFlagInvisible | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker));
    CHECK(source.textureFlags == 0x0034u);
    CHECK((source.channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics) != 0);
    CHECK((source.channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelHelper) != 0);
}

TEST_CASE("MM9 DAT physics query raycasts are channel-aware")
{
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view = syntheticQueryView();

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = vec3(0.25f, 0.25f, 2.0f);
    ray.direction = vec3(0.0f, 0.0f, -5.0f);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> physicsHit =
        OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options);
    REQUIRE(physicsHit.has_value());
    CHECK(physicsHit->source.sourceModelName == "PhysicsBSP");
    CHECK(physicsHit->distance == doctest::Approx(1.0f));
    checkVec3Approx(physicsHit->point, vec3(0.25f, 0.25f, 1.0f));

    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible;
    const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> visibleHit =
        OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options);
    REQUIRE(visibleHit.has_value());
    CHECK(visibleHit->source.sourceModelName == "VisibleModel");
    CHECK(visibleHit->distance == doctest::Approx(2.0f));

    options.channelMask =
        OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible | OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> combinedHit =
        OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options);
    REQUIRE(combinedHit.has_value());
    CHECK(combinedHit->source.sourceModelName == "PhysicsBSP");
}

TEST_CASE("MM9 DAT physics query reports hit material flags and plane facts")
{
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view = syntheticQueryView();

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = vec3(0.25f, 0.25f, 2.0f);
    ray.direction = vec3(0.0f, 0.0f, -1.0f);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> hit =
        OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->source.surfaceFlags == (
        OpenYAMM::Game::Mm9DatSurfaceFlagInvisible | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker));
    CHECK(hit->source.textureFlags == 0x0034u);
    CHECK(hit->normal.x == doctest::Approx(0.0f));
    CHECK(hit->normal.y == doctest::Approx(0.0f));
    CHECK(hit->normal.z == doctest::Approx(1.0f));
    CHECK(hit->planeDistance == doctest::Approx(1.0f));
    CHECK(std::isfinite(hit->distance));
    CHECK(std::isfinite(hit->barycentricU));
    CHECK(std::isfinite(hit->barycentricV));
}

TEST_CASE("MM9 DAT physics query supports backface culling, max distance, and zero direction rejection")
{
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view = syntheticQueryView();

    OpenYAMM::Game::Mm9DatPickRay backfaceRay = {};
    backfaceRay.origin = vec3(0.25f, 0.25f, -1.0f);
    backfaceRay.direction = vec3(0.0f, 0.0f, 1.0f);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible;
    options.includeBackfaces = false;
    CHECK_FALSE(OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, backfaceRay, options).has_value());

    options.includeBackfaces = true;
    CHECK(OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, backfaceRay, options).has_value());

    OpenYAMM::Game::Mm9DatPickRay zeroRay = {};
    zeroRay.origin = vec3(0.25f, 0.25f, 2.0f);
    zeroRay.direction = vec3(0.0f, 0.0f, 0.0f);
    CHECK_FALSE(OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, zeroRay, options).has_value());

    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    CHECK_FALSE(
        OpenYAMM::Game::segmentcastMm9DatPhysicsQueryView(
            view,
            vec3(0.25f, 0.25f, 2.0f),
            vec3(0.25f, 0.25f, 1.25f),
            options).has_value());
    CHECK(
        OpenYAMM::Game::segmentcastMm9DatPhysicsQueryView(
            view,
            vec3(0.25f, 0.25f, 2.0f),
            vec3(0.25f, 0.25f, 0.75f),
            options).has_value());
}

TEST_CASE("MM9 DAT physics query does not fall back from missing physics geometry")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(renderTriangle(0, 1, 2, 0.0f, "VisibleOnly", OpenYAMM::Game::Mm9DatSurfaceFlagSolid, 0));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    filters.entries.push_back(filterEntry(0, OpenYAMM::Game::Mm9DatRenderFilterVisual));

    const OpenYAMM::Game::Mm9DatPhysicsQueryView view =
        OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);

    REQUIRE(view.triangles.size() == 1);
    CHECK_FALSE(view.stats.hasPhysicsGeometry);
    CHECK_FALSE(view.stats.warnings.empty());

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = vec3(0.25f, 0.25f, 1.0f);
    ray.direction = vec3(0.0f, 0.0f, -1.0f);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    CHECK_FALSE(OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options).has_value());

    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible;
    CHECK(OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options).has_value());
}

TEST_CASE("MM9 DAT physics query uses deterministic equal-distance tie breaking")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(renderTriangle(0, 1, 2, 0.0f, "First", OpenYAMM::Game::Mm9DatSurfaceFlagSolid, 0));
    mesh.triangles.push_back(renderTriangle(1, 3, 4, 0.0f, "Second", OpenYAMM::Game::Mm9DatSurfaceFlagSolid, 0));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    filters.entries.push_back(filterEntry(1, OpenYAMM::Game::Mm9DatRenderFilterPhysics));
    filters.entries.push_back(filterEntry(0, OpenYAMM::Game::Mm9DatRenderFilterPhysics));

    const OpenYAMM::Game::Mm9DatPhysicsQueryView view =
        OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = vec3(0.25f, 0.25f, 1.0f);
    ray.direction = vec3(0.0f, 0.0f, -1.0f);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> hit =
        OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->source.renderTriangleIndex == 0);
    CHECK(hit->source.sourceModelName == "First");
}

TEST_CASE("MM9 DAT physics query movement helper projects velocity along a plane")
{
    const OpenYAMM::Game::Mm9DatVec3 wallProjection =
        OpenYAMM::Game::projectMm9DatPhysicsVelocityAlongPlane(vec3(-4.0f, 3.0f, 2.0f), vec3(1.0f, 0.0f, 0.0f));
    checkVec3Approx(wallProjection, vec3(0.0f, 3.0f, 2.0f));

    const OpenYAMM::Game::Mm9DatVec3 floorProjection =
        OpenYAMM::Game::projectMm9DatPhysicsVelocityAlongPlane(vec3(4.0f, 0.0f, 2.0f), vec3(0.0f, 1.0f, 0.0f));
    checkVec3Approx(floorProjection, vec3(4.0f, 0.0f, 2.0f));
}

TEST_CASE("MM9 DAT physics query builds from real DAT helper geometry")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Editor::EditorMm9DatWorldSidecar sidecar = loadDatWorldSidecar("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);
    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(
            mesh,
            modelRolesFromSidecar(sidecar),
            sidecar.userPortals.size());
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view =
        OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);

    REQUIRE(view.triangles.size() == mesh.triangles.size());
    CHECK(view.stats.physicsTriangles > 0);
    CHECK(view.stats.visibilityTriangles > 0);
    CHECK(view.stats.hasPhysicsGeometry);
    CHECK(view.stats.hasVisibilityGeometry);
    CHECK(view.stats.warnings.empty());
}

TEST_CASE("MM9 DAT physics query raycasts real DAT physics and visible channels")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Editor::EditorMm9DatWorldSidecar sidecar = loadDatWorldSidecar("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);
    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(
            mesh,
            modelRolesFromSidecar(sidecar),
            sidecar.userPortals.size());
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view =
        OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);

    std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> selectedPhysicsHit;
    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions physicsOptions = {};
    physicsOptions.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;

    for (const OpenYAMM::Game::Mm9DatPhysicsQueryTriangle &triangle : view.triangles)
    {
        if ((triangle.source.channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics) == 0)
        {
            continue;
        }

        const OpenYAMM::Game::Mm9DatPickRay ray = centerRayForQueryTriangle(triangle, 2.0f);
        const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> hit =
            OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, physicsOptions);

        if (hit && hit->source.renderTriangleIndex == triangle.source.renderTriangleIndex)
        {
            selectedPhysicsHit = hit;
            break;
        }
    }

    REQUIRE(selectedPhysicsHit.has_value());
    CHECK((selectedPhysicsHit->channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics) != 0);
    CHECK(selectedPhysicsHit->source.sourceModelIndex < world.worldModels.size());
    const OpenYAMM::Game::Mm9DatWorldModel &physicsModel =
        world.worldModels[selectedPhysicsHit->source.sourceModelIndex];
    CHECK(selectedPhysicsHit->source.sourcePolyIndex < physicsModel.polies.size());
    CHECK(selectedPhysicsHit->source.sourceSurfaceIndex < physicsModel.surfaces.size());

    std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> selectedVisibleHit;
    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions visibleOptions = {};
    visibleOptions.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible;

    for (const OpenYAMM::Game::Mm9DatPhysicsQueryTriangle &triangle : view.triangles)
    {
        if ((triangle.source.channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible) == 0
            || (triangle.source.channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics) != 0)
        {
            continue;
        }

        const OpenYAMM::Game::Mm9DatPickRay ray = centerRayForQueryTriangle(triangle, 2.0f);
        const std::optional<OpenYAMM::Game::Mm9DatPhysicsRayHit> hit =
            OpenYAMM::Game::raycastMm9DatPhysicsQueryView(view, ray, visibleOptions);

        if (hit && hit->source.renderTriangleIndex == triangle.source.renderTriangleIndex)
        {
            selectedVisibleHit = hit;
            break;
        }
    }

    REQUIRE(selectedVisibleHit.has_value());
    CHECK((selectedVisibleHit->channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelVisible) != 0);
    CHECK((selectedVisibleHit->channelFlags & OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics) == 0);
}
