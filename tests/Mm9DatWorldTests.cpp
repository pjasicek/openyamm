#include "doctest/doctest.h"

#include "editor/document/Mm9DatLevelMetadata.h"
#include "game/mm9/Mm9DatWorld.h"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <cmath>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace
{
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

OpenYAMM::Game::Mm9DatVec3 triangleVertexPosition(
    const OpenYAMM::Game::Mm9DatRenderTriangle &triangle,
    size_t vertexIndex)
{
    return {
        triangle.vertices[vertexIndex].x,
        triangle.vertices[vertexIndex].y,
        triangle.vertices[vertexIndex].z,
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

OpenYAMM::Game::Mm9DatVec3 multiply(const OpenYAMM::Game::Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

OpenYAMM::Game::Mm9DatVec3 cross(
    const OpenYAMM::Game::Mm9DatVec3 &left,
    const OpenYAMM::Game::Mm9DatVec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
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

std::optional<OpenYAMM::Game::Mm9DatVec3> triangleNormal(
    const OpenYAMM::Game::Mm9DatRenderTriangle &triangle)
{
    const OpenYAMM::Game::Mm9DatVec3 vertex0 = triangleVertexPosition(triangle, 0);
    const OpenYAMM::Game::Mm9DatVec3 vertex1 = triangleVertexPosition(triangle, 1);
    const OpenYAMM::Game::Mm9DatVec3 vertex2 = triangleVertexPosition(triangle, 2);
    const OpenYAMM::Game::Mm9DatVec3 normal = cross(subtract(vertex1, vertex0), subtract(vertex2, vertex0));
    const float normalLength = length(normal);

    if (normalLength <= 0.0001f)
    {
        return std::nullopt;
    }

    return OpenYAMM::Game::Mm9DatVec3{
        normal.x / normalLength,
        normal.y / normalLength,
        normal.z / normalLength,
    };
}

OpenYAMM::Game::Mm9DatVec3 triangleCenter(const OpenYAMM::Game::Mm9DatRenderTriangle &triangle)
{
    const OpenYAMM::Game::Mm9DatVec3 vertex0 = triangleVertexPosition(triangle, 0);
    const OpenYAMM::Game::Mm9DatVec3 vertex1 = triangleVertexPosition(triangle, 1);
    const OpenYAMM::Game::Mm9DatVec3 vertex2 = triangleVertexPosition(triangle, 2);

    return {
        (vertex0.x + vertex1.x + vertex2.x) / 3.0f,
        (vertex0.y + vertex1.y + vertex2.y) / 3.0f,
        (vertex0.z + vertex1.z + vertex2.z) / 3.0f,
    };
}

std::optional<OpenYAMM::Game::Mm9DatPickRay> centerRayForTriangle(
    const OpenYAMM::Game::Mm9DatRenderTriangle &triangle,
    float offset)
{
    const std::optional<OpenYAMM::Game::Mm9DatVec3> normal = triangleNormal(triangle);

    if (!normal)
    {
        return std::nullopt;
    }

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = add(triangleCenter(triangle), multiply(*normal, offset));
    ray.direction = multiply(*normal, -1.0f);
    return ray;
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

TEST_CASE("MM9 DAT parser loads source world models matching generated sidecars")
{
    const std::vector<std::string> mapIds = {
        "thjorgard",
        "thronheimcity",
        "dungeonofsecrets",
    };

    for (const std::string &mapId : mapIds)
    {
        CAPTURE(mapId);

        const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld(mapId);
        const OpenYAMM::Editor::EditorMm9DatWorldSidecar sidecar = loadDatWorldSidecar(mapId);

        CHECK(world.version == 66);
        CHECK(world.worldModels.size() == sidecar.worldModels.size());
        CHECK(world.worldModels.size() == sidecar.totals.worldModelCount);
        CHECK(!world.worldInfo.propertyString.empty());

        for (size_t modelIndex = 0; modelIndex < world.worldModels.size(); ++modelIndex)
        {
            const OpenYAMM::Game::Mm9DatWorldModel &model = world.worldModels[modelIndex];
            const OpenYAMM::Editor::EditorMm9DatWorldModelSummary &summary = sidecar.worldModels[modelIndex];

            CHECK(model.name == summary.sourceName);
            CHECK(model.pointsLt.size() == summary.pointCount);
            CHECK(model.planes.size() == summary.planeCount);
            CHECK(model.surfaces.size() == summary.surfaceCount);
            CHECK(model.polies.size() == summary.polyCount);
            CHECK(model.leaves.size() == summary.leafCount);
            CHECK(model.nodes.size() == summary.nodeCount);
            CHECK(model.userPortals.size() == summary.userPortalCount);
            CHECK(model.textures.size() == summary.textureCount);
            CHECK(model.rootNodeIndex == summary.rootNodeIndex);
            CHECK(model.sectionCount == summary.sectionCount);
            CHECK(model.pblockTable.recordCount == summary.pblockTable.recordCount.value_or(0));
        }
    }
}

TEST_CASE("MM9 DAT render mesh preserves source polygon surface and texture ids")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Editor::EditorMm9DatWorldSidecar sidecar = loadDatWorldSidecar("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);

    CHECK(mesh.sourcePolyCount == sidecar.totals.sourcePolyCount);
    CHECK(mesh.triangles.size() > mesh.sourcePolyCount);
    CHECK(mesh.skippedPolyCount == 0);
    CHECK(mesh.skippedDegenerateTriangleCount > 0);

    bool foundTriangulatedSourcePolygon = false;
    bool foundInvisibleHelperSurface = false;

    for (const OpenYAMM::Game::Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        REQUIRE(triangle.sourceModelIndex < world.worldModels.size());
        const OpenYAMM::Game::Mm9DatWorldModel &model = world.worldModels[triangle.sourceModelIndex];
        REQUIRE(triangle.sourcePolyIndex < model.polies.size());
        REQUIRE(triangle.sourceSurfaceIndex < model.surfaces.size());
        REQUIRE(triangle.sourceTextureIndex < model.textures.size());

        const OpenYAMM::Game::Mm9DatPoly &poly = model.polies[triangle.sourcePolyIndex];
        const OpenYAMM::Game::Mm9DatSurface &surface = model.surfaces[triangle.sourceSurfaceIndex];

        CHECK(triangle.sourceSurfaceIndex == poly.surfaceIndex);
        CHECK(triangle.sourceTextureIndex == surface.textureIndex);
        CHECK(triangle.sourceTexture == model.textures[surface.textureIndex]);
        CHECK(triangle.surfaceFlags == surface.flags);
        CHECK(triangle.textureFlags == surface.textureFlags);

        for (const OpenYAMM::Game::Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            CHECK(std::isfinite(vertex.x));
            CHECK(std::isfinite(vertex.y));
            CHECK(std::isfinite(vertex.z));
            CHECK(std::isfinite(vertex.uPixels));
            CHECK(std::isfinite(vertex.vPixels));
        }

        foundTriangulatedSourcePolygon = foundTriangulatedSourcePolygon || poly.vertices.size() > 3;
        foundInvisibleHelperSurface = foundInvisibleHelperSurface || ((triangle.surfaceFlags & 0x00000004u) != 0);
    }

    CHECK(foundTriangulatedSourcePolygon);
    CHECK(foundInvisibleHelperSurface);
}

TEST_CASE("MM9 DAT render mesh picking returns DAT source ids")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);

    REQUIRE(!mesh.triangles.empty());
    CHECK(!OpenYAMM::Game::pickMm9DatRenderMesh(mesh, {}).has_value());

    std::optional<OpenYAMM::Game::Mm9DatRenderMeshPickHit> selectedHit;
    size_t selectedTriangleIndex = std::numeric_limits<size_t>::max();

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        const OpenYAMM::Game::Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
        const std::optional<OpenYAMM::Game::Mm9DatPickRay> ray = centerRayForTriangle(triangle, 2.0f);

        if (!ray)
        {
            continue;
        }

        const std::optional<OpenYAMM::Game::Mm9DatRenderMeshPickHit> hit =
            OpenYAMM::Game::pickMm9DatRenderMesh(mesh, *ray);

        if (hit && hit->triangleIndex == triangleIndex)
        {
            selectedHit = hit;
            selectedTriangleIndex = triangleIndex;
            break;
        }
    }

    REQUIRE(selectedHit.has_value());
    REQUIRE(selectedTriangleIndex < mesh.triangles.size());

    const OpenYAMM::Game::Mm9DatRenderTriangle &triangle = mesh.triangles[selectedTriangleIndex];
    const OpenYAMM::Game::Mm9DatVec3 center = triangleCenter(triangle);

    CHECK(selectedHit->sourceModelIndex == triangle.sourceModelIndex);
    CHECK(selectedHit->sourcePolyIndex == triangle.sourcePolyIndex);
    CHECK(selectedHit->sourceSurfaceIndex == triangle.sourceSurfaceIndex);
    CHECK(selectedHit->sourceTextureIndex == triangle.sourceTextureIndex);
    CHECK(selectedHit->sourceModelName == triangle.sourceModelName);
    CHECK(selectedHit->sourceTexture == triangle.sourceTexture);
    CHECK(selectedHit->distance > 0.0f);
    CHECK(std::fabs(selectedHit->position.x - center.x) < 0.01f);
    CHECK(std::fabs(selectedHit->position.y - center.y) < 0.01f);
    CHECK(std::fabs(selectedHit->position.z - center.z) < 0.01f);
    CHECK(selectedHit->barycentricU >= -0.001f);
    CHECK(selectedHit->barycentricV >= -0.001f);
    CHECK(selectedHit->barycentricU + selectedHit->barycentricV <= 1.001f);
}

TEST_CASE("MM9 DAT render mesh material assignment uses map-local aliases")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = 7;
    triangle.sourcePolyIndex = 11;
    triangle.sourceSurfaceIndex = 13;
    triangle.sourceTextureIndex = 2;
    triangle.sourceTexture = "TEXTURES\\Test\\Wall.dtx";
    mesh.triangles.push_back(triangle);

    std::vector<OpenYAMM::Game::Mm9DatMaterialPreview> materials;
    OpenYAMM::Game::Mm9DatMaterialPreview material = {};
    material.materialIndex = 5;
    material.alias = "WALL";
    material.sourceTexture = "textures/test/wall.dtx";
    material.resolvedSourcePath = "source/textures/test/wall.dtx";
    material.resolvedPreviewPath = "maps/test.bitmaps/WALL.bmp";
    material.sourceDtxResolved = true;
    material.previewCacheAvailable = true;
    materials.push_back(material);

    const std::vector<OpenYAMM::Game::Mm9DatRenderMaterialAssignment> assignments =
        OpenYAMM::Game::assignMm9DatRenderMeshMaterials(mesh, materials);

    REQUIRE(assignments.size() == 1);
    CHECK(assignments[0].triangleIndex == 0);
    CHECK(assignments[0].sourceModelIndex == triangle.sourceModelIndex);
    CHECK(assignments[0].sourcePolyIndex == triangle.sourcePolyIndex);
    CHECK(assignments[0].sourceSurfaceIndex == triangle.sourceSurfaceIndex);
    CHECK(assignments[0].sourceTextureIndex == triangle.sourceTextureIndex);
    CHECK(assignments[0].sourceTexture == triangle.sourceTexture);
    CHECK(assignments[0].assigned);
    CHECK(!assignments[0].ambiguous);
    CHECK(assignments[0].materialCandidateCount == 1);
    CHECK(assignments[0].materialIndex == material.materialIndex);
    CHECK(assignments[0].alias == material.alias);
    CHECK(assignments[0].resolvedSourcePath == material.resolvedSourcePath);
    CHECK(assignments[0].resolvedPreviewPath == material.resolvedPreviewPath);
    CHECK(assignments[0].sourceDtxResolved);
    CHECK(assignments[0].previewCacheAvailable);

    materials.push_back(material);
    materials.back().materialIndex = 6;
    materials.back().alias = "WALL_DUPLICATE";

    const std::vector<OpenYAMM::Game::Mm9DatRenderMaterialAssignment> ambiguousAssignments =
        OpenYAMM::Game::assignMm9DatRenderMeshMaterials(mesh, materials);

    REQUIRE(ambiguousAssignments.size() == 1);
    CHECK(!ambiguousAssignments[0].assigned);
    CHECK(ambiguousAssignments[0].ambiguous);
    CHECK(ambiguousAssignments[0].materialCandidateCount == 2);

    const std::vector<OpenYAMM::Game::Mm9DatRenderMaterialAssignment> missingAssignments =
        OpenYAMM::Game::assignMm9DatRenderMeshMaterials(mesh, {});

    REQUIRE(missingAssignments.size() == 1);
    CHECK(!missingAssignments[0].assigned);
    CHECK(!missingAssignments[0].ambiguous);
    CHECK(missingAssignments[0].materialCandidateCount == 0);
}

TEST_CASE("MM9 DAT render mesh bounds and camera frame are finite")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);
    const OpenYAMM::Game::Mm9DatRenderBounds bounds = OpenYAMM::Game::computeMm9DatRenderBounds(mesh);

    REQUIRE(bounds.valid);
    CHECK(bounds.radius > 0.0f);
    CHECK(bounds.min.x < bounds.max.x);
    CHECK(bounds.min.y < bounds.max.y);
    CHECK(bounds.min.z < bounds.max.z);
    CHECK(std::isfinite(bounds.center.x));
    CHECK(std::isfinite(bounds.center.y));
    CHECK(std::isfinite(bounds.center.z));

    bool foundBoundaryVertex = false;

    for (const OpenYAMM::Game::Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        for (const OpenYAMM::Game::Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            CHECK(vertex.x >= bounds.min.x - 0.01f);
            CHECK(vertex.x <= bounds.max.x + 0.01f);
            CHECK(vertex.y >= bounds.min.y - 0.01f);
            CHECK(vertex.y <= bounds.max.y + 0.01f);
            CHECK(vertex.z >= bounds.min.z - 0.01f);
            CHECK(vertex.z <= bounds.max.z + 0.01f);

            foundBoundaryVertex = foundBoundaryVertex
                || std::fabs(vertex.x - bounds.min.x) < 0.01f
                || std::fabs(vertex.x - bounds.max.x) < 0.01f
                || std::fabs(vertex.y - bounds.min.y) < 0.01f
                || std::fabs(vertex.y - bounds.max.y) < 0.01f
                || std::fabs(vertex.z - bounds.min.z) < 0.01f
                || std::fabs(vertex.z - bounds.max.z) < 0.01f;
        }
    }

    CHECK(foundBoundaryVertex);

    const OpenYAMM::Game::Mm9DatCameraFrame frame = OpenYAMM::Game::frameMm9DatRenderMeshCamera(mesh);

    REQUIRE(frame.valid);
    CHECK(std::isfinite(frame.position.x));
    CHECK(std::isfinite(frame.position.y));
    CHECK(std::isfinite(frame.position.z));
    CHECK(frame.radius == bounds.radius);
    CHECK(frame.nearPlane >= 1.0f);
    CHECK(frame.farPlane > frame.nearPlane);
    CHECK(length(subtract(frame.position, frame.target)) > frame.radius);
}

TEST_CASE("MM9 DAT render mesh filters classify roles and surface flags")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};

    OpenYAMM::Game::Mm9DatRenderTriangle visualTriangle = {};
    visualTriangle.sourceModelIndex = 0;
    visualTriangle.sourcePolyIndex = 1;
    visualTriangle.sourceSurfaceIndex = 2;
    mesh.triangles.push_back(visualTriangle);

    OpenYAMM::Game::Mm9DatRenderTriangle physicsTriangle = {};
    physicsTriangle.sourceModelIndex = 1;
    physicsTriangle.sourcePolyIndex = 3;
    physicsTriangle.sourceSurfaceIndex = 4;
    physicsTriangle.surfaceFlags = OpenYAMM::Game::Mm9DatSurfaceFlagInvisible;
    mesh.triangles.push_back(physicsTriangle);

    OpenYAMM::Game::Mm9DatRenderTriangle skyTriangle = {};
    skyTriangle.sourceModelIndex = 2;
    skyTriangle.sourcePolyIndex = 5;
    skyTriangle.sourceSurfaceIndex = 6;
    mesh.triangles.push_back(skyTriangle);

    std::vector<OpenYAMM::Game::Mm9DatModelRenderRole> roles;
    OpenYAMM::Game::Mm9DatModelRenderRole visualRole = {};
    visualRole.sourceModelIndex = 0;
    visualRole.visible = true;
    roles.push_back(visualRole);

    OpenYAMM::Game::Mm9DatModelRenderRole physicsRole = {};
    physicsRole.sourceModelIndex = 1;
    physicsRole.physicsBsp = true;
    roles.push_back(physicsRole);

    OpenYAMM::Game::Mm9DatModelRenderRole skyRole = {};
    skyRole.sourceModelIndex = 2;
    skyRole.visible = true;
    skyRole.sky = true;
    roles.push_back(skyRole);

    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(mesh, roles, 4);

    REQUIRE(filters.entries.size() == 3);
    CHECK(filters.summary.totalTriangles == 3);
    CHECK(filters.summary.visualTriangles == 2);
    CHECK(filters.summary.invisibleTriangles == 1);
    CHECK(filters.summary.skyTriangles == 1);
    CHECK(filters.summary.helperTriangles == 1);
    CHECK(filters.summary.physicsTriangles == 1);
    CHECK(filters.summary.portalOverlays == 4);
    CHECK(filters.summary.unclassifiedTriangles == 0);
    CHECK(filters.entries[0].sourceModelIndex == 0);
    CHECK(filters.entries[0].sourcePolyIndex == 1);
    CHECK(filters.entries[0].sourceSurfaceIndex == 2);
    CHECK(filters.entries[1].sourceModelIndex == 1);
    CHECK(filters.entries[1].sourcePolyIndex == 3);
    CHECK(filters.entries[1].sourceSurfaceIndex == 4);
    CHECK(filters.entries[2].sourceModelIndex == 2);
    CHECK(filters.entries[2].sourcePolyIndex == 5);
    CHECK(filters.entries[2].sourceSurfaceIndex == 6);
    CHECK((filters.entries[0].flags & OpenYAMM::Game::Mm9DatRenderFilterVisual) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterPhysics) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterInvisible) != 0);
    CHECK((filters.entries[2].flags & OpenYAMM::Game::Mm9DatRenderFilterSky) != 0);
}

TEST_CASE("MM9 DAT mechanism preview transforms target model without mutating source mesh")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};

    OpenYAMM::Game::Mm9DatRenderTriangle targetTriangle = {};
    targetTriangle.sourceModelIndex = 7;
    targetTriangle.sourcePolyIndex = 11;
    targetTriangle.sourceSurfaceIndex = 13;
    targetTriangle.sourceTextureIndex = 17;
    targetTriangle.sourceModelName = "DoorA";
    targetTriangle.vertices[0].x = 0.0f;
    targetTriangle.vertices[0].y = 0.0f;
    targetTriangle.vertices[0].z = 0.0f;
    targetTriangle.vertices[1].x = 1.0f;
    targetTriangle.vertices[1].y = 0.0f;
    targetTriangle.vertices[1].z = 0.0f;
    targetTriangle.vertices[2].x = 0.0f;
    targetTriangle.vertices[2].y = 1.0f;
    targetTriangle.vertices[2].z = 0.0f;
    mesh.triangles.push_back(targetTriangle);

    OpenYAMM::Game::Mm9DatRenderTriangle staticTriangle = targetTriangle;
    staticTriangle.sourceModelIndex = 8;
    staticTriangle.sourceModelName = "StaticA";
    staticTriangle.vertices[0].x = 10.0f;
    staticTriangle.vertices[1].x = 11.0f;
    staticTriangle.vertices[2].x = 10.0f;
    mesh.triangles.push_back(staticTriangle);

    OpenYAMM::Game::Mm9DatMechanismPreviewMotion motion = {};
    motion.sourceModelIndex = 7;
    motion.progress = 1.0f;
    motion.hasLinearMotion = true;
    motion.moveDirLt = {2.0f, 0.0f, 0.0f};
    motion.moveDistLt = 3.0f;

    const OpenYAMM::Game::Mm9DatMechanismPreviewResult preview =
        OpenYAMM::Game::buildMm9DatMechanismPreviewMesh(mesh, motion, 1.0f);

    REQUIRE(preview.targetFound);
    CHECK(preview.transformedTriangles == 1);
    CHECK(preview.boundsChanged);
    REQUIRE(preview.previewMesh.triangles.size() == 2);
    CHECK(mesh.triangles[0].vertices[0].x == doctest::Approx(0.0f));
    CHECK(preview.previewMesh.triangles[0].sourceModelIndex == mesh.triangles[0].sourceModelIndex);
    CHECK(preview.previewMesh.triangles[0].sourcePolyIndex == mesh.triangles[0].sourcePolyIndex);
    CHECK(preview.previewMesh.triangles[0].vertices[0].x == doctest::Approx(6.0f));
    CHECK(preview.previewMesh.triangles[1].vertices[0].x == doctest::Approx(mesh.triangles[1].vertices[0].x));
}

TEST_CASE("MM9 DAT surface flag constants match LithTech references")
{
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagSolid == (1u << 0));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagNonexistent == (1u << 1));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagInvisible == (1u << 2));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagTransparent == (1u << 3));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagSky == (1u << 4));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagPortal == (1u << 13));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker == (1u << 17));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagVisibilityBlocker == (1u << 21));
    CHECK(OpenYAMM::Game::Mm9DatSurfaceFlagNotAStep == (1u << 22));
}

TEST_CASE("MM9 DAT render mesh filters classify real helper geometry")
{
    const OpenYAMM::Game::Mm9DatWorld world = loadSourceDatWorld("thjorgard");
    const OpenYAMM::Editor::EditorMm9DatWorldSidecar sidecar = loadDatWorldSidecar("thjorgard");
    const OpenYAMM::Game::Mm9DatRenderMesh mesh = OpenYAMM::Game::buildMm9DatRenderMesh(world);
    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(
            mesh,
            modelRolesFromSidecar(sidecar),
            sidecar.userPortals.size());

    REQUIRE(filters.entries.size() == mesh.triangles.size());
    CHECK(filters.summary.totalTriangles == mesh.triangles.size());
    CHECK(filters.summary.visualTriangles > 0);
    CHECK(filters.summary.invisibleTriangles > 0);
    CHECK(filters.summary.helperTriangles > 0);
    CHECK(filters.summary.railTriangles > 0);
    CHECK(filters.summary.physicsTriangles > 0);
    CHECK(filters.summary.visibilityTriangles > 0);
    CHECK(filters.summary.portalOverlays == sidecar.userPortals.size());
    CHECK(filters.summary.unclassifiedTriangles == 0);

    for (const OpenYAMM::Game::Mm9DatRenderFilterEntry &entry : filters.entries)
    {
        if ((entry.flags & OpenYAMM::Game::Mm9DatRenderFilterRail) != 0)
        {
            CHECK((entry.flags & OpenYAMM::Game::Mm9DatRenderFilterHelper) != 0);
            CHECK((entry.flags & OpenYAMM::Game::Mm9DatRenderFilterVisual) == 0);
        }
    }
}

TEST_CASE("MM9 DAT render mesh filters split visible water from water volumes")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};

    OpenYAMM::Game::Mm9DatRenderTriangle oceanTriangle = {};
    oceanTriangle.sourceModelIndex = 0;
    oceanTriangle.sourceModelName = "Ocean";
    oceanTriangle.sourceTexture = "Sprites\\Water\\Ocean4.spr";
    mesh.triangles.push_back(oceanTriangle);

    OpenYAMM::Game::Mm9DatRenderTriangle markerTriangle = {};
    markerTriangle.sourceModelIndex = 1;
    markerTriangle.sourceModelName = "BlueWater2";
    markerTriangle.sourceTexture = "TEXTURES\\LevelTextures\\Terrain\\WaterMarker.dtx";
    mesh.triangles.push_back(markerTriangle);

    std::vector<OpenYAMM::Game::Mm9DatModelRenderRole> roles;
    OpenYAMM::Game::Mm9DatModelRenderRole oceanRole = {};
    oceanRole.sourceModelIndex = 0;
    oceanRole.visible = true;
    oceanRole.water = true;
    roles.push_back(oceanRole);

    OpenYAMM::Game::Mm9DatModelRenderRole markerRole = {};
    markerRole.sourceModelIndex = 1;
    markerRole.visible = true;
    markerRole.water = true;
    roles.push_back(markerRole);

    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(mesh, roles, 0);

    REQUIRE(filters.entries.size() == 2);
    CHECK(filters.summary.waterTriangles == 2);
    CHECK(filters.summary.visibleWaterTriangles == 1);
    CHECK(filters.summary.waterVolumeTriangles == 1);
    CHECK(filters.summary.helperTriangles == 1);
    CHECK(filters.summary.visualTriangles == 1);
    CHECK((filters.entries[0].flags & OpenYAMM::Game::Mm9DatRenderFilterVisibleWater) != 0);
    CHECK((filters.entries[0].flags & OpenYAMM::Game::Mm9DatRenderFilterWaterVolume) == 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterWaterVolume) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterHelper) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterVisual) == 0);
}

TEST_CASE("MM9 DAT render mesh filters classify AI rail containers as helper geometry")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};

    OpenYAMM::Game::Mm9DatRenderTriangle wallTriangle = {};
    wallTriangle.sourceModelIndex = 0;
    wallTriangle.sourceModelName = "CastleWall";
    wallTriangle.sourceTexture = "TEXTURES\\LevelTextures\\City\\wall.dtx";
    mesh.triangles.push_back(wallTriangle);

    OpenYAMM::Game::Mm9DatRenderTriangle railTriangle = {};
    railTriangle.sourceModelIndex = 1;
    railTriangle.sourceModelName = "AITrk42";
    railTriangle.sourceTexture = "TEXTURES\\LevelTextures\\Misc\\rail.dtx";
    mesh.triangles.push_back(railTriangle);

    std::vector<OpenYAMM::Game::Mm9DatModelRenderRole> roles;
    OpenYAMM::Game::Mm9DatModelRenderRole wallRole = {};
    wallRole.sourceModelIndex = 0;
    wallRole.visible = true;
    roles.push_back(wallRole);

    OpenYAMM::Game::Mm9DatModelRenderRole railRole = {};
    railRole.sourceModelIndex = 1;
    railRole.visible = true;
    roles.push_back(railRole);

    const OpenYAMM::Game::Mm9DatRenderFilterResult filters =
        OpenYAMM::Game::classifyMm9DatRenderMeshFilters(mesh, roles, 0);

    REQUIRE(filters.entries.size() == 2);
    CHECK(filters.summary.visualTriangles == 1);
    CHECK(filters.summary.helperTriangles == 1);
    CHECK(filters.summary.railTriangles == 1);
    CHECK((filters.entries[0].flags & OpenYAMM::Game::Mm9DatRenderFilterVisual) != 0);
    CHECK((filters.entries[0].flags & OpenYAMM::Game::Mm9DatRenderFilterRail) == 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterRail) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterHelper) != 0);
    CHECK((filters.entries[1].flags & OpenYAMM::Game::Mm9DatRenderFilterVisual) == 0);
}
