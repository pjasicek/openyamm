#include "doctest/doctest.h"

#include "game/mm9/Mm9DatLevelRuntimeLoader.h"
#include "game/mm9/Mm9AnimatedActorBinding.h"
#include "game/mm9/Mm9AnimatedModelResolver.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/mm9/Mm9DatPartyRuntime.h"
#include "game/mm9/Mm9DatRuntimeDevEntry.h"
#include "game/mm9/Mm9DatSceneRuntime.h"
#include "game/mm9/Mm9DatWorldRenderer.h"
#include "game/mm9/Mm9DatWorldRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/gameplay/GameplayInputFrame.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
OpenYAMM::Game::Mm9DatRenderTriangle floorTriangle()
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = 7;
    triangle.sourcePolyIndex = 11;
    triangle.sourceSurfaceIndex = 13;
    triangle.sourceTextureIndex = 17;
    triangle.sourceModelName = "PhysicsBSP";
    triangle.sourceTexture = "floor.dtx";
    triangle.surfaceFlags = OpenYAMM::Game::Mm9DatSurfaceFlagInvisible
        | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker;
    triangle.vertices[0] = {-512.0f, 0.0f, -512.0f, 0.0f, 0.0f};
    triangle.vertices[1] = {512.0f, 0.0f, -512.0f, 0.0f, 0.0f};
    triangle.vertices[2] = {0.0f, 0.0f, 512.0f, 0.0f, 0.0f};
    return triangle;
}

OpenYAMM::Game::Mm9DatRenderTriangle wallTriangle()
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = 8;
    triangle.sourcePolyIndex = 12;
    triangle.sourceSurfaceIndex = 14;
    triangle.sourceTextureIndex = 18;
    triangle.sourceModelName = "PhysicsBSP";
    triangle.sourceTexture = "wall.dtx";
    triangle.surfaceFlags = OpenYAMM::Game::Mm9DatSurfaceFlagInvisible
        | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker;
    triangle.vertices[0] = {64.0f, -512.0f, -512.0f, 0.0f, 0.0f};
    triangle.vertices[1] = {64.0f, 512.0f, 0.0f, 0.0f, 0.0f};
    triangle.vertices[2] = {64.0f, -512.0f, 512.0f, 0.0f, 0.0f};
    return triangle;
}

OpenYAMM::Game::Mm9DatRenderTriangle lowStepWallTriangle()
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = 9;
    triangle.sourcePolyIndex = 19;
    triangle.sourceSurfaceIndex = 29;
    triangle.sourceTextureIndex = 39;
    triangle.sourceModelName = "PhysicsBSP";
    triangle.sourceTexture = "step.dtx";
    triangle.surfaceFlags = OpenYAMM::Game::Mm9DatSurfaceFlagInvisible
        | OpenYAMM::Game::Mm9DatSurfaceFlagPhysicsBlocker;
    triangle.vertices[0] = {64.0f, 0.0f, -512.0f, 0.0f, 0.0f};
    triangle.vertices[1] = {64.0f, 80.0f, 0.0f, 0.0f, 0.0f};
    triangle.vertices[2] = {64.0f, 0.0f, 512.0f, 0.0f, 0.0f};
    return triangle;
}

OpenYAMM::Game::Mm9DatRenderTriangle visualTriangle(
    size_t sourceModelIndex,
    const std::string &sourceTexture,
    float xOffset)
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = {};
    triangle.sourceModelIndex = sourceModelIndex;
    triangle.sourcePolyIndex = sourceModelIndex + 10;
    triangle.sourceSurfaceIndex = sourceModelIndex + 20;
    triangle.sourceTextureIndex = sourceModelIndex + 30;
    triangle.sourceModelName = "VisualModel" + std::to_string(sourceModelIndex);
    triangle.sourceTexture = sourceTexture;
    triangle.vertices[0] = {xOffset, 0.0f, 0.0f, 0.0f, 0.0f};
    triangle.vertices[1] = {xOffset + 10.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    triangle.vertices[2] = {xOffset, 0.0f, 10.0f, 0.0f, 0.0f};
    return triangle;
}

OpenYAMM::Game::Mm9DatObjectProperty datStringProperty(
    const std::string &name,
    const std::string &value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = {};
    property.name = name;
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::String;
    property.code = 0;
    property.decoded = true;
    property.stringValue = value;
    return property;
}

OpenYAMM::Game::Mm9DatObjectProperty datVec3Property(
    const std::string &name,
    const OpenYAMM::Game::Mm9DatVec3 &value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = {};
    property.name = name;
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::Vector;
    property.code = 1;
    property.decoded = true;
    property.vectorValue = value;
    return property;
}

OpenYAMM::Game::Mm9DatObjectProperty datColorProperty(
    const std::string &name,
    const OpenYAMM::Game::Mm9DatVec3 &value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = datVec3Property(name, value);
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::Color;
    property.code = 2;
    return property;
}

bool isFiniteVec3(const OpenYAMM::Game::Mm9DatVec3 &value)
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

OpenYAMM::Game::Mm9DatObjectProperty datRealProperty(const std::string &name, float value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = {};
    property.name = name;
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::Real;
    property.code = 3;
    property.decoded = true;
    property.floatValue = value;
    return property;
}

OpenYAMM::Game::Mm9DatObjectProperty datIntegerProperty(const std::string &name, int value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = {};
    property.name = name;
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::LongInt;
    property.code = 6;
    property.decoded = true;
    property.intValue = value;
    return property;
}

OpenYAMM::Game::Mm9DatObjectProperty datBoolProperty(const std::string &name, bool value)
{
    OpenYAMM::Game::Mm9DatObjectProperty property = {};
    property.name = name;
    property.type = OpenYAMM::Game::Mm9DatObjectPropertyType::Bool;
    property.code = 5;
    property.decoded = true;
    property.boolValue = value;
    property.intValue = value ? 1 : 0;
    return property;
}

OpenYAMM::Game::Mm9DatPhysicsQueryView syntheticPhysicsQueryView(bool includeWall = false)
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(floorTriangle());
    if (includeWall)
    {
        mesh.triangles.push_back(wallTriangle());
    }

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = OpenYAMM::Game::Mm9DatRenderFilterPhysics
            | OpenYAMM::Game::Mm9DatRenderFilterHelper
            | OpenYAMM::Game::Mm9DatRenderFilterInvisible;
        filters.entries.push_back(entry);
    }

    return OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);
}

OpenYAMM::Game::Mm9DatCollisionWorld syntheticCollisionWorld(bool includeWall = false)
{
    const OpenYAMM::Game::Mm9DatPhysicsQueryView view = syntheticPhysicsQueryView(includeWall);
    OpenYAMM::Game::Mm9DatCollisionWorld world = {};
    REQUIRE(world.build(view));
    return world;
}

OpenYAMM::Game::Mm9DatCollisionWorld syntheticStepCollisionWorld()
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(floorTriangle());
    mesh.triangles.push_back(lowStepWallTriangle());

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = OpenYAMM::Game::Mm9DatRenderFilterPhysics
            | OpenYAMM::Game::Mm9DatRenderFilterHelper
            | OpenYAMM::Game::Mm9DatRenderFilterInvisible;
        filters.entries.push_back(entry);
    }

    const OpenYAMM::Game::Mm9DatPhysicsQueryView view =
        OpenYAMM::Game::buildMm9DatPhysicsQueryView(mesh, filters);
    OpenYAMM::Game::Mm9DatCollisionWorld world = {};
    REQUIRE(world.build(view));
    return world;
}

OpenYAMM::Game::Mm9ScriptedObject scriptedObject(
    size_t sourceObjectIndex,
    const std::string &sourceClass,
    bool moveToFloor,
    bool flying)
{
    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.sourceObjectIndex = sourceObjectIndex;
    object.objectId = "object_" + std::to_string(sourceObjectIndex);
    object.sourceClass = sourceClass;
    object.sourceName = object.objectId;
    object.x = 0.0f;
    object.y = 512.0f;
    object.z = 0.0f;
    object.radius = 32.0f;
    object.height = 128.0f;
    object.visible = true;
    object.solid = true;
    object.rayHit = true;
    object.movement.moveToFloor = moveToFloor;
    object.movement.flying = flying;
    return object;
}

OpenYAMM::Game::Mm9ScriptedObject scriptedObjectAt(
    size_t sourceObjectIndex,
    const OpenYAMM::Game::Mm9DatVec3 &position)
{
    OpenYAMM::Game::Mm9ScriptedObject object =
        scriptedObject(sourceObjectIndex, "Prop", false, false);
    object.x = position.x;
    object.y = position.y;
    object.z = position.z;
    object.radius = 16.0f;
    object.height = 128.0f;
    return object;
}

std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

std::filesystem::path levelPathForMap(const std::string &mapId)
{
    return sourceRoot() / "assets_dev/worlds/mm9/maps" / (mapId + ".level.yml");
}

OpenYAMM::Game::AnimatedModelAsset loadMm9ResolvedModel(
    const OpenYAMM::Game::Mm9AnimatedModelResolution &resolution)
{
    std::string errorMessage;
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(resolution.modelAssetPath, errorMessage);
    REQUIRE_MESSAGE(asset.has_value(), errorMessage.c_str());

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(resolution.modelSidecarPath, errorMessage);
    REQUIRE_MESSAGE(sidecar.has_value(), errorMessage.c_str());

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    REQUIRE_FALSE(asset->hasErrors());
    return *asset;
}

}

TEST_CASE("MM9 DAT collision world segmentcasts through spatial cells")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld world = syntheticCollisionWorld(true);

    OpenYAMM::Game::Mm9DatPhysicsRaycastOptions options = {};
    options.channelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    const std::optional<OpenYAMM::Game::Mm9DatCollisionRayHit> hit =
        world.segmentcast({0.0f, 64.0f, 0.0f}, {128.0f, 64.0f, 0.0f}, options);

    REQUIRE(hit.has_value());
    CHECK(hit->hit.point.x == doctest::Approx(64.0f));
    CHECK(hit->hit.source.sourceModelIndex == 8);
    CHECK(hit->candidateTriangleCount > 0);
    CHECK(hit->testedTriangleCount > 0);
}

TEST_CASE("MM9 DAT collision world resolves floor support through spatial cells")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld world = syntheticCollisionWorld();

    OpenYAMM::Game::Mm9DatFloorSupportQuery query = {};
    query.position = {0.0f, 512.0f, 0.0f};
    query.halfHeight = 64.0f;

    const std::optional<OpenYAMM::Game::Mm9DatFloorSupportHit> support = world.findFloorSupport(query);

    REQUIRE(support.has_value());
    CHECK(support->floorPoint.y == doctest::Approx(0.0f));
    CHECK(support->adjustedPosition.x == doctest::Approx(0.0f));
    CHECK(support->adjustedPosition.y == doctest::Approx(64.1f));
    CHECK(support->adjustedPosition.z == doctest::Approx(0.0f));
    CHECK(support->source.sourceModelIndex == 7);
    CHECK(support->candidateTriangleCount > 0);
    CHECK(support->testedTriangleCount > 0);
    CHECK(world.stats().cellCount > 0);
}

TEST_CASE("MM9 DAT render world groups normal visual triangles and skips helper geometry")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "stone.dtx", 0.0f));
    mesh.triangles.push_back(visualTriangle(0, "stone.dtx", 16.0f));
    mesh.triangles.push_back(floorTriangle());

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = triangleIndex < 2
            ? OpenYAMM::Game::Mm9DatRenderFilterVisual
            : OpenYAMM::Game::Mm9DatRenderFilterPhysics | OpenYAMM::Game::Mm9DatRenderFilterHelper;
        filters.entries.push_back(entry);
    }

    const OpenYAMM::Game::Mm9DatRenderWorld renderWorld =
        OpenYAMM::Game::buildMm9DatRenderWorld(mesh, filters);

    REQUIRE(renderWorld.partitions.size() == 1);
    CHECK(renderWorld.partitions[0].triangleIndices.size() == 2);
    CHECK(renderWorld.stats.normalVisualTriangleCount == 2);
    CHECK(renderWorld.stats.helperSkippedTriangleCount == 1);
    CHECK(renderWorld.stats.partitionCount == 1);
    CHECK(renderWorld.stats.opaquePartitionCount == 1);
}

TEST_CASE("MM9 DAT render world keeps visible water renderable and skips water volumes")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "ocean.dtx", 0.0f));
    mesh.triangles.push_back(visualTriangle(1, "watermarker.dtx", 16.0f));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};

    OpenYAMM::Game::Mm9DatRenderFilterEntry visibleWater = {};
    visibleWater.triangleIndex = 0;
    visibleWater.sourceModelIndex = 0;
    visibleWater.flags =
        OpenYAMM::Game::Mm9DatRenderFilterVisual
        | OpenYAMM::Game::Mm9DatRenderFilterWater
        | OpenYAMM::Game::Mm9DatRenderFilterVisibleWater;
    filters.entries.push_back(visibleWater);

    OpenYAMM::Game::Mm9DatRenderFilterEntry waterVolume = {};
    waterVolume.triangleIndex = 1;
    waterVolume.sourceModelIndex = 1;
    waterVolume.flags =
        OpenYAMM::Game::Mm9DatRenderFilterWater
        | OpenYAMM::Game::Mm9DatRenderFilterWaterVolume
        | OpenYAMM::Game::Mm9DatRenderFilterHelper;
    filters.entries.push_back(waterVolume);

    const OpenYAMM::Game::Mm9DatRenderWorld renderWorld =
        OpenYAMM::Game::buildMm9DatRenderWorld(mesh, filters);

    REQUIRE(renderWorld.partitions.size() == 1);
    CHECK(renderWorld.partitions[0].triangleIndices.size() == 1);
    CHECK(renderWorld.partitions[0].triangleIndices[0] == 0);
    CHECK(renderWorld.stats.normalVisualTriangleCount == 1);
    CHECK(renderWorld.stats.visibleWaterTriangleCount == 1);
    CHECK(renderWorld.stats.waterVolumeSkippedTriangleCount == 1);
    CHECK(renderWorld.stats.helperSkippedTriangleCount == 1);
}

TEST_CASE("MM9 DAT prepared render world builds stable static vertex and index sections")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "stone.dtx", 0.0f));
    mesh.triangles.push_back(visualTriangle(0, "stone.dtx", 16.0f));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = OpenYAMM::Game::Mm9DatRenderFilterVisual;
        filters.entries.push_back(entry);
    }

    const OpenYAMM::Game::Mm9DatRenderWorld renderWorld =
        OpenYAMM::Game::buildMm9DatRenderWorld(mesh, filters);
    const OpenYAMM::Game::Mm9DatMechanismRenderWorld mechanismRenderWorld = {};
    const OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld =
        OpenYAMM::Game::buildMm9DatPreparedRenderWorld(
            mesh,
            renderWorld,
            mechanismRenderWorld,
            filters);

    REQUIRE(preparedRenderWorld.sections.size() == 1);
    CHECK(preparedRenderWorld.vertices.size() == 6);
    CHECK(preparedRenderWorld.indices.size() == 6);
    CHECK(preparedRenderWorld.stats.staticSectionCount == 1);
    CHECK(preparedRenderWorld.stats.dynamicSectionCount == 0);
    CHECK(preparedRenderWorld.stats.staticTriangleCount == 2);
    CHECK(preparedRenderWorld.sections[0].materialKey == "source:stone.dtx");
    CHECK(preparedRenderWorld.sections[0].vertexStart == 0);
    CHECK(preparedRenderWorld.sections[0].vertexCount == 6);
    CHECK(preparedRenderWorld.sections[0].indexStart == 0);
    CHECK(preparedRenderWorld.sections[0].indexCount == 6);
    CHECK(preparedRenderWorld.sections[0].sourceTriangleIndices.size() == 2);
    CHECK(preparedRenderWorld.vertices[3].x == doctest::Approx(16.0f));
}

TEST_CASE("MM9 DAT render submission plan emits grouped draw commands and culls by bounds")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "stone.dtx", 0.0f));
    mesh.triangles.push_back(visualTriangle(1, "", 4096.0f));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = OpenYAMM::Game::Mm9DatRenderFilterVisual;
        filters.entries.push_back(entry);
    }

    const OpenYAMM::Game::Mm9DatRenderWorld renderWorld =
        OpenYAMM::Game::buildMm9DatRenderWorld(mesh, filters);
    OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld =
        OpenYAMM::Game::buildMm9DatPreparedRenderWorld(
            mesh,
            renderWorld,
            {},
            filters);
    const OpenYAMM::Game::Mm9DatRuntimeMaterialTable materialTable =
        OpenYAMM::Game::buildMm9DatRuntimeMaterialTable(preparedRenderWorld);

    const OpenYAMM::Game::Mm9DatRenderSubmissionPlan fullPlan =
        OpenYAMM::Game::buildMm9DatRenderSubmissionPlan(preparedRenderWorld);

    REQUIRE(materialTable.materials.size() == 2);
    CHECK(materialTable.stats.sourceTextureMaterialCount == 1);
    CHECK(materialTable.stats.missingMaterialCount == 1);
    CHECK(materialTable.stats.textureCacheEligibleCount == 1);
    CHECK(materialTable.materials[0].materialKey == "source:stone.dtx");
    CHECK(materialTable.materials[0].materialIndex == 0);
    CHECK(materialTable.materials[0].sourceTexture == "stone.dtx");
    CHECK(materialTable.materials[0].textureCacheEligible);
    CHECK(materialTable.materials[1].materialKey == "missing");
    CHECK(materialTable.materials[1].materialIndex == 1);
    CHECK(materialTable.materials[1].missing);
    CHECK(preparedRenderWorld.sections[0].materialIndex == 0);
    CHECK(preparedRenderWorld.sections[1].materialIndex == 1);
    REQUIRE(fullPlan.commands.size() == 2);
    CHECK(fullPlan.stats.drawCallCount == 2);
    CHECK(fullPlan.stats.submittedTriangleCount == 2);
    CHECK(fullPlan.stats.textureMissDrawCallCount == 1);
    CHECK(fullPlan.commands[0].materialIndex == 0);
    CHECK(fullPlan.commands[0].indexCount == 3);
    CHECK(fullPlan.commands[0].triangleCount == 1);

    OpenYAMM::Game::Mm9DatRenderSubmissionOptions options = {};
    options.cullByDistance = true;
    options.viewPosition = {0.0f, 0.0f, 0.0f};
    options.maxVisibleDistance = 512.0f;
    const OpenYAMM::Game::Mm9DatRenderSubmissionPlan culledPlan =
        OpenYAMM::Game::buildMm9DatRenderSubmissionPlan(preparedRenderWorld, options);

    REQUIRE(culledPlan.commands.size() == 1);
    CHECK(culledPlan.commands[0].sourceModelIndex == 0);
    CHECK(culledPlan.stats.visibleSectionCount == 1);
    CHECK(culledPlan.stats.culledSectionCount == 1);
    CHECK(culledPlan.stats.submittedTriangleCount == 1);
}

TEST_CASE("MM9 DAT render upload plan splits immutable static and updateable dynamic geometry")
{
    OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld = {};
    preparedRenderWorld.vertices = {
        {0.0f, 0.0f, 0.0f, 0.0f, 0.0f},
        {16.0f, 0.0f, 0.0f, 16.0f, 0.0f},
        {0.0f, 0.0f, 16.0f, 0.0f, 16.0f},
        {32.0f, 0.0f, 0.0f, 0.0f, 0.0f},
        {48.0f, 0.0f, 0.0f, 16.0f, 0.0f},
        {32.0f, 0.0f, 16.0f, 0.0f, 16.0f},
    };
    preparedRenderWorld.indices = {0, 1, 2, 3, 4, 5};

    OpenYAMM::Game::Mm9DatPreparedRenderSection staticSection = {};
    staticSection.sectionIndex = 0;
    staticSection.materialIndex = 7;
    staticSection.vertexStart = 0;
    staticSection.vertexCount = 3;
    staticSection.indexStart = 0;
    staticSection.indexCount = 3;
    preparedRenderWorld.sections.push_back(staticSection);

    OpenYAMM::Game::Mm9DatPreparedRenderSection dynamicSection = {};
    dynamicSection.sectionIndex = 1;
    dynamicSection.dynamic = true;
    dynamicSection.materialIndex = 8;
    dynamicSection.vertexStart = 3;
    dynamicSection.vertexCount = 3;
    dynamicSection.indexStart = 3;
    dynamicSection.indexCount = 3;
    preparedRenderWorld.sections.push_back(dynamicSection);

    const OpenYAMM::Game::Mm9DatWorldRenderUploadPlan uploadPlan =
        OpenYAMM::Game::buildMm9DatWorldRenderUploadPlan(preparedRenderWorld);

    REQUIRE(uploadPlan.sections.size() == 2);
    CHECK(uploadPlan.stats.staticSectionCount == 1);
    CHECK(uploadPlan.stats.dynamicSectionCount == 1);
    CHECK(uploadPlan.stats.staticVertexCount == 3);
    CHECK(uploadPlan.stats.staticIndexCount == 3);
    CHECK(uploadPlan.stats.dynamicVertexCount == 3);
    CHECK(uploadPlan.stats.dynamicIndexCount == 3);
    CHECK(uploadPlan.stats.invalidIndexCount == 0);
    CHECK(uploadPlan.sections[0].bufferKind == OpenYAMM::Game::Mm9DatWorldRenderBufferKind::Static);
    CHECK(uploadPlan.sections[0].materialIndex == 7);
    CHECK(uploadPlan.sections[1].bufferKind == OpenYAMM::Game::Mm9DatWorldRenderBufferKind::Dynamic);
    CHECK(uploadPlan.sections[1].materialIndex == 8);
    CHECK(uploadPlan.staticIndices[2] == 2);
    CHECK(uploadPlan.dynamicIndices[0] == 0);
    CHECK(uploadPlan.dynamicVertices[1].x == doctest::Approx(48.0f));
}

TEST_CASE("MM9 DAT render upload converts DAT coordinates and scales DTX pixel UVs")
{
    OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld = {};
    preparedRenderWorld.vertices = {
        {1.0f, 2.0f, 3.0f, 32.0f, 16.0f},
        {4.0f, 5.0f, 6.0f, 64.0f, 32.0f},
        {7.0f, 8.0f, 9.0f, 96.0f, 48.0f},
    };
    preparedRenderWorld.indices = {0, 1, 2};

    OpenYAMM::Game::Mm9DatPreparedRenderSection section = {};
    section.sectionIndex = 0;
    section.materialIndex = 7;
    section.vertexStart = 0;
    section.vertexCount = 3;
    section.indexStart = 0;
    section.indexCount = 3;
    preparedRenderWorld.sections.push_back(section);

    OpenYAMM::Game::Mm9DatWorldRenderUploadPlan uploadPlan =
        OpenYAMM::Game::buildMm9DatWorldRenderUploadPlan(preparedRenderWorld);

    OpenYAMM::Game::Mm9DatWorldTextureResource texture = {};
    texture.materialIndex = 7;
    texture.width = 128;
    texture.height = 64;
    texture.loaded = true;

    OpenYAMM::Game::Mm9DatWorldTextureResources textureResources = {};
    textureResources.textures.push_back(texture);

    OpenYAMM::Game::applyMm9DatWorldTextureUvScale(uploadPlan, textureResources);

    REQUIRE(uploadPlan.staticVertices.size() == 3);
    CHECK(uploadPlan.staticVertices[0].x == doctest::Approx(1.0f));
    CHECK(uploadPlan.staticVertices[0].y == doctest::Approx(3.0f));
    CHECK(uploadPlan.staticVertices[0].z == doctest::Approx(2.0f));
    CHECK(uploadPlan.staticVertices[1].u == doctest::Approx(0.5f));
    CHECK(uploadPlan.staticVertices[1].v == doctest::Approx(0.5f));
}

TEST_CASE("MM9 DAT render submit plan maps draw commands to uploaded sections and loaded textures")
{
    OpenYAMM::Game::Mm9DatWorldRenderUploadPlan uploadPlan = {};

    OpenYAMM::Game::Mm9DatWorldRenderUploadSection staticSection = {};
    staticSection.sectionIndex = 10;
    staticSection.bufferKind = OpenYAMM::Game::Mm9DatWorldRenderBufferKind::Static;
    staticSection.materialIndex = 7;
    staticSection.vertexStart = 0;
    staticSection.vertexCount = 3;
    staticSection.indexStart = 0;
    staticSection.indexCount = 3;
    uploadPlan.sections.push_back(staticSection);

    OpenYAMM::Game::Mm9DatWorldRenderUploadSection dynamicSection = {};
    dynamicSection.sectionIndex = 20;
    dynamicSection.bufferKind = OpenYAMM::Game::Mm9DatWorldRenderBufferKind::Dynamic;
    dynamicSection.materialIndex = 8;
    dynamicSection.blendMode = OpenYAMM::Game::Mm9DatRenderPartitionBlendMode::Translucent;
    dynamicSection.vertexStart = 0;
    dynamicSection.vertexCount = 3;
    dynamicSection.indexStart = 0;
    dynamicSection.indexCount = 6;
    uploadPlan.sections.push_back(dynamicSection);

    OpenYAMM::Game::Mm9DatWorldRenderUploadSection missingTextureSection = {};
    missingTextureSection.sectionIndex = 30;
    missingTextureSection.materialIndex = 9;
    missingTextureSection.vertexStart = 3;
    missingTextureSection.vertexCount = 3;
    missingTextureSection.indexStart = 3;
    missingTextureSection.indexCount = 3;
    uploadPlan.sections.push_back(missingTextureSection);

    OpenYAMM::Game::Mm9DatWorldTextureResources textures = {};
    OpenYAMM::Game::Mm9DatWorldTextureResource staticTexture = {};
    staticTexture.materialIndex = 7;
    staticTexture.textureHandle.idx = 1;
    staticTexture.loaded = true;
    textures.textures.push_back(staticTexture);

    OpenYAMM::Game::Mm9DatWorldTextureResource dynamicTexture = {};
    dynamicTexture.materialIndex = 8;
    dynamicTexture.textureHandle.idx = 2;
    dynamicTexture.loaded = true;
    textures.textures.push_back(dynamicTexture);

    OpenYAMM::Game::Mm9DatRenderSubmissionPlan runtimePlan = {};
    OpenYAMM::Game::Mm9DatRenderDrawCommand staticCommand = {};
    staticCommand.sectionIndex = 10;
    runtimePlan.commands.push_back(staticCommand);

    OpenYAMM::Game::Mm9DatRenderDrawCommand dynamicCommand = {};
    dynamicCommand.sectionIndex = 20;
    runtimePlan.commands.push_back(dynamicCommand);

    OpenYAMM::Game::Mm9DatRenderDrawCommand missingTextureCommand = {};
    missingTextureCommand.sectionIndex = 30;
    runtimePlan.commands.push_back(missingTextureCommand);

    OpenYAMM::Game::Mm9DatRenderDrawCommand missingSectionCommand = {};
    missingSectionCommand.sectionIndex = 40;
    runtimePlan.commands.push_back(missingSectionCommand);

    const OpenYAMM::Game::Mm9DatWorldRenderSubmitPlan submitPlan =
        OpenYAMM::Game::buildMm9DatWorldRenderSubmitPlan(runtimePlan, uploadPlan, textures);

    REQUIRE(submitPlan.commands.size() == 2);
    CHECK(submitPlan.stats.sourceCommandCount == 4);
    CHECK(submitPlan.stats.submittedCommandCount == 2);
    CHECK(submitPlan.stats.staticCommandCount == 1);
    CHECK(submitPlan.stats.dynamicCommandCount == 1);
    CHECK(submitPlan.stats.skippedMissingSectionCount == 1);
    CHECK(submitPlan.stats.skippedMissingTextureCount == 1);
    CHECK(submitPlan.stats.submittedTriangleCount == 3);
    CHECK(submitPlan.stats.submittedIndexCount == 9);
    CHECK(submitPlan.commands[0].sectionIndex == 10);
    CHECK(submitPlan.commands[0].textureResourceIndex == 0);
    CHECK(submitPlan.commands[1].sectionIndex == 20);
    CHECK(submitPlan.commands[1].textureResourceIndex == 1);
    CHECK(submitPlan.commands[1].blendMode == OpenYAMM::Game::Mm9DatRenderPartitionBlendMode::Translucent);
}

TEST_CASE("MM9 DAT runtime texture catalog resolves material ids without sidecars")
{
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dat_runtime_texture_catalog_test";
    std::filesystem::remove_all(root);
    std::filesystem::create_directories(root / "SubDir");

    {
        std::ofstream textureFile(root / "SubDir" / "STONE.DTX", std::ios::binary);
        textureFile << "not a real dtx; catalog only resolves paths";
    }

    OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld = {};
    OpenYAMM::Game::Mm9DatPreparedRenderSection section = {};
    section.sectionIndex = 0;
    section.materialKey = "source:stone.dtx";
    section.indexCount = 3;
    preparedRenderWorld.sections.push_back(section);

    OpenYAMM::Game::Mm9DatPreparedRenderSection missingSection = {};
    missingSection.sectionIndex = 1;
    missingSection.materialKey = "missing";
    missingSection.indexCount = 3;
    preparedRenderWorld.sections.push_back(missingSection);

    const OpenYAMM::Game::Mm9DatRuntimeMaterialTable materialTable =
        OpenYAMM::Game::buildMm9DatRuntimeMaterialTable(preparedRenderWorld);
    const OpenYAMM::Game::Mm9DatRuntimeTextureCatalog catalog =
        OpenYAMM::Game::buildMm9DatRuntimeTextureCatalog({root});
    const OpenYAMM::Game::Mm9DatRuntimeTextureBindings bindings =
        OpenYAMM::Game::bindMm9DatRuntimeTextures(materialTable, catalog);

    REQUIRE(catalog.entries.size() == 1);
    CHECK(catalog.stats.sourceRootCount == 1);
    CHECK(catalog.stats.dtxFileCount == 1);
    CHECK(catalog.stats.catalogKeyCount == 3);
    REQUIRE(bindings.bindings.size() == 1);
    CHECK(bindings.stats.materialLookupCount == 1);
    CHECK(bindings.stats.resolvedMaterialCount == 1);
    CHECK(bindings.stats.missingMaterialCount == 0);
    CHECK(bindings.bindings[0].materialIndex == 0);
    CHECK(bindings.bindings[0].resolved);
    CHECK(bindings.bindings[0].physicalPath.filename().generic_string() == "STONE.DTX");

    std::filesystem::remove_all(root);
}

TEST_CASE("MM9 DAT world runtime builds light and sky layers directly from DAT objects")
{
    OpenYAMM::Game::Mm9DatWorld world = {};
    world.worldInfo.propertyString = "AmbientLight 10 20 30";
    world.worldInfo.extentsMinLt = {-100.0f, -100.0f, -100.0f};
    world.worldInfo.extentsMaxLt = {100.0f, 100.0f, 100.0f};
    OpenYAMM::Game::Mm9DatWorldModel skyModel = {};
    skyModel.name = "SkyDome";
    world.worldModels.push_back(std::move(skyModel));

    OpenYAMM::Game::Mm9DatObject lightObject = {};
    lightObject.sourceObjectIndex = 1;
    lightObject.className = "Light";
    lightObject.properties.push_back(datStringProperty("Name", "TorchLight"));
    lightObject.properties.push_back(datVec3Property("Pos", {10.0f, 20.0f, 30.0f}));
    lightObject.properties.push_back(datRealProperty("LightRadius", 128.0f));
    lightObject.properties.push_back(datColorProperty("LightColor", {255.0f, 128.0f, 64.0f}));
    lightObject.properties.push_back(datBoolProperty("LightObjects", true));
    lightObject.properties.push_back(datBoolProperty("FastLightObjects", false));
    world.objects.push_back(std::move(lightObject));

    OpenYAMM::Game::Mm9DatObject skyObject = {};
    skyObject.sourceObjectIndex = 2;
    skyObject.className = "DemoSkyWorldModel";
    skyObject.properties.push_back(datStringProperty("Name", "SkyDome"));
    skyObject.properties.push_back(datVec3Property("Pos", {0.0f, 0.0f, 0.0f}));
    skyObject.properties.push_back(datVec3Property("SkyDims", {50.0f, 50.0f, 50.0f}));
    skyObject.properties.push_back(datRealProperty("InnerPercentX", 0.5f));
    skyObject.properties.push_back(datRealProperty("InnerPercentY", 0.5f));
    skyObject.properties.push_back(datRealProperty("InnerPercentZ", 0.5f));
    skyObject.properties.push_back(datIntegerProperty("Index", 0));
    world.objects.push_back(std::move(skyObject));

    OpenYAMM::Game::Mm9DatModelRenderRole skyRole = {};
    skyRole.sourceModelIndex = 0;
    skyRole.sky = true;

    OpenYAMM::Game::Mm9DatWorldRuntimeBuildInput input = {};
    input.mapId = "test";
    input.pWorld = &world;
    input.modelRoles.push_back(skyRole);

    const OpenYAMM::Game::Mm9DatWorldRuntime runtime =
        OpenYAMM::Game::buildMm9DatWorldRuntime(input);

    CHECK(runtime.lightLayer.worldInfo.hasAmbientLight);
    REQUIRE(runtime.lightLayer.lights.size() == 1);
    CHECK(runtime.lightLayer.lights[0].sourceName == "TorchLight");
    CHECK(runtime.lightLayer.lights[0].hasPosition);
    CHECK(runtime.lightLayer.lights[0].positionLt.z == doctest::Approx(30.0f));
    CHECK(runtime.lightLayer.lights[0].staticObjectLightEligible);
    REQUIRE(runtime.staticRenderLights.size() == 1);
    CHECK(runtime.stats.lightCount == 1);
    CHECK(runtime.stats.staticRenderLightCount == 1);

    REQUIRE(runtime.skyLayer.definitions.size() == 1);
    REQUIRE(runtime.skyLayer.objects.size() == 1);
    CHECK(runtime.skyLayer.objects[0].hasSourceModel);
    CHECK(runtime.skyLayer.skyModelIndices.size() == 1);
    REQUIRE(runtime.activeSkyDef.has_value());
    CHECK(runtime.activeSkyDef->sourceName == "SkyDome");
    CHECK(runtime.skyCameraMap.has_value());
    CHECK(runtime.stats.skyDefinitionCount == 1);
    CHECK(runtime.stats.skyObjectCount == 1);
    CHECK(runtime.stats.skyModelCount == 1);
}

TEST_CASE("MM9 DAT party movement snaps to floor and slides along wall collision")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld world = syntheticCollisionWorld(true);

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {0.0f, 64.1f, 0.0f};
    step.desiredDisplacement = {128.0f, 0.0f, 32.0f};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 96.0f;

    const OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatParty(world, step);

    CHECK(movement.blockedByWall);
    CHECK(movement.slidAlongWall);
    CHECK(movement.onGround);
    REQUIRE(movement.wallHit.has_value());
    REQUIRE(movement.floorHit.has_value());
    CHECK(movement.finalPosition.x == doctest::Approx(56.2389f));
    CHECK(movement.finalPosition.y == doctest::Approx(64.1f));
    CHECK(movement.finalPosition.z == doctest::Approx(32.0f));
    CHECK(movement.wallCandidateTriangleCount > 0);
    CHECK(movement.wallTestedTriangleCount > 0);
    CHECK(movement.floorCandidateTriangleCount > 0);
    CHECK(movement.floorTestedTriangleCount > 0);
}

TEST_CASE("MM9 DAT party movement steps over low static collision when raised trace clears")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld world = syntheticStepCollisionWorld();

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {0.0f, 64.1f, 0.0f};
    step.desiredDisplacement = {128.0f, 0.0f, 0.0f};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 96.0f;
    step.maxStepHeight = 0.0f;

    OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatParty(world, step);

    CHECK(movement.blockedByWall);
    CHECK_FALSE(movement.steppedUp);
    CHECK(movement.finalPosition.x < 128.0f);

    step.maxStepHeight = 32.0f;
    movement = OpenYAMM::Game::moveMm9DatParty(world, step);

    CHECK_FALSE(movement.blockedByWall);
    CHECK(movement.steppedUp);
    CHECK(movement.onGround);
    REQUIRE(movement.floorHit.has_value());
    CHECK(movement.finalPosition.x == doctest::Approx(128.0f));
    CHECK(movement.finalPosition.y == doctest::Approx(64.1f));
    CHECK(movement.finalPosition.z == doctest::Approx(0.0f));
    CHECK(movement.wallCandidateTriangleCount > 0);
    CHECK(movement.wallTestedTriangleCount > 0);
    CHECK(movement.floorCandidateTriangleCount > 0);
    CHECK(movement.floorTestedTriangleCount > 0);
}

TEST_CASE("MM9 DAT runtime party movement collides with indexed solid objects")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    OpenYAMM::Game::Mm9ScriptedObject object = scriptedObjectAt(77, {96.0f, 64.1f, 0.0f});
    object.objectId = "solid_prop_77";
    object.sourceName = "SolidProp77";
    object.radius = 16.0f;
    object.height = 128.0f;
    object.solid = true;
    runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry({object}, runtime.collisionWorld);
    REQUIRE(runtime.objectRegistry.stats.collidableObjectCount == 1);
    CHECK(runtime.objectRegistry.stats.collidableCellCount > 0);
    CHECK(runtime.objectRegistry.stats.collidableCellObjectRefs > 0);

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {0.0f, 64.1f, 0.0f};
    step.desiredDisplacement = {128.0f, 0.0f, 0.0f};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 96.0f;

    const OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatPartyInWorldRuntime(runtime, step);

    CHECK(movement.blockedByObject);
    CHECK_FALSE(movement.blockedByWall);
    CHECK(movement.onGround);
    REQUIRE(movement.objectHit.has_value());
    CHECK(movement.objectHit->objectId == "solid_prop_77");
    CHECK(movement.objectHit->sourceObjectIndex == 77);
    CHECK(movement.objectHit->sourceClass == "Prop");
    CHECK(movement.objectCandidateCount == 1);
    CHECK(movement.objectTestedCount == 1);
    CHECK(movement.finalPosition.x == doctest::Approx(64.0f));
    CHECK(movement.finalPosition.y == doctest::Approx(64.1f));
    CHECK(movement.finalPosition.z == doctest::Approx(0.0f));
}

TEST_CASE("MM9 DAT runtime party movement collides with transformed mechanism triangles")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    runtime.renderMesh.triangles.push_back(wallTriangle());

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    OpenYAMM::Game::Mm9EventTriggerOutput triggerOutput = {};
    triggerOutput.phase = "open";
    triggerOutput.slot = 0;
    triggerOutput.targetName = "DoorRelay";
    triggerOutput.messageName = "On";
    mechanism.triggerOutputs.push_back(triggerOutput);
    OpenYAMM::Game::Mm9EventMechanismSound sound = {};
    sound.phase = "open_start";
    sound.sourceProperty = "OpenStartSound";
    sound.soundName = "stone_door_open";
    sound.authored = true;
    mechanism.sounds.push_back(sound);
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 8;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);
    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    REQUIRE(runtime.mechanismRuntime.stats.activeMechanismCount == 1);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 1);
    CHECK(runtime.mechanismCollisionCache.stats.batchCount == 1);
    CHECK(runtime.mechanismCollisionCache.stats.indexedBatchCount == 1);
    REQUIRE(runtime.mechanismCollisionCache.batchIndexByMechanismHandle.count(
        runtime.mechanismRuntime.mechanisms[0].handle) == 1);
    CHECK(runtime.mechanismCollisionCache.stats.transformedTriangleCount == 1);

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {0.0f, 64.1f, 0.0f};
    step.desiredDisplacement = {128.0f, 0.0f, 0.0f};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 96.0f;

    const OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatPartyInWorldRuntime(runtime, step);

    CHECK(movement.blockedByMechanism);
    CHECK_FALSE(movement.blockedByWall);
    CHECK(movement.onGround);
    REQUIRE(movement.mechanismHit.has_value());
    CHECK(movement.mechanismHit->mechanismHandle == runtime.mechanismRuntime.mechanisms[0].handle);
    CHECK(movement.mechanismHit->mechanismId == "mech_0");
    CHECK(movement.mechanismHit->objectId == "door_0");
    CHECK(movement.mechanismHit->sourceModelIndex == 8);
    CHECK(movement.mechanismHit->sourceObjectIndex == 42);
    CHECK(movement.finalPosition.x == doctest::Approx(56.0f));
    CHECK(movement.finalPosition.y == doctest::Approx(64.1f));
    CHECK(movement.mechanismCandidateCount > 0);
    CHECK(movement.mechanismTestedCount > 0);
    CHECK(movement.mechanismCandidateTriangleCount > 0);
    CHECK(movement.mechanismTestedTriangleCount > 0);
    CHECK_FALSE(movement.mechanismContactCommandAttempted);
    CHECK(runtime.mechanismRuntime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closed);
}

TEST_CASE("MM9 DAT runtime party movement opens touch-triggered mechanisms on contact")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    runtime.renderMesh.triangles.push_back(wallTriangle());

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.activation.touchToOpen = true;
    mechanism.activation.hasTouchToOpen = true;
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 8;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.preparedRenderWorld =
        OpenYAMM::Game::buildMm9DatPreparedRenderWorld(
            runtime.renderMesh,
            runtime.renderWorld,
            runtime.mechanismRenderWorld,
            runtime.renderFilters);
    runtime.renderSubmissionPlan =
        OpenYAMM::Game::buildMm9DatRenderSubmissionPlan(runtime.preparedRenderWorld);

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {0.0f, 64.1f, 0.0f};
    step.desiredDisplacement = {128.0f, 0.0f, 0.0f};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 96.0f;

    const OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatPartyInWorldRuntime(runtime, step);

    CHECK(movement.blockedByMechanism);
    CHECK(movement.mechanismContactCommandAttempted);
    CHECK(movement.mechanismContactCommand.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(movement.mechanismContactCommand.stateChanged);
    CHECK(runtime.mechanismRuntime.mechanisms[0].touchToOpen);
    CHECK(runtime.mechanismRuntime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
    CHECK(runtime.mechanismRuntime.movingMechanismIndices.size() == 1);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 1);
    CHECK(runtime.mechanismCollisionCache.stats.indexedBatchCount == 1);
}

TEST_CASE("MM9 DAT runtime party movement snaps floor support to transformed mechanism triangles")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "platform.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "platform_0";
    mechanism.objectId = "platform_object_0";
    mechanism.sourceObjectIndex = 55;
    mechanism.sourceClass = "Elevator";
    mechanism.sourceName = "Platform0";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "platform_object_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "PlatformModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);

    OpenYAMM::Game::Mm9DatPartyMovementStep step = {};
    step.position = {5.0f, 128.0f, 5.0f};
    step.desiredDisplacement = {};
    step.radius = 8.0f;
    step.halfHeight = 64.0f;
    step.floorSnapDistance = 256.0f;

    const OpenYAMM::Game::Mm9DatPartyMovementResult movement =
        OpenYAMM::Game::moveMm9DatPartyInWorldRuntime(runtime, step);

    CHECK(movement.onGround);
    REQUIRE(movement.floorHit.has_value());
    REQUIRE(movement.mechanismFloorHit.has_value());
    CHECK(movement.mechanismFloorHit->mechanismId == "platform_0");
    CHECK(movement.mechanismFloorHit->objectId == "platform_object_0");
    CHECK(movement.mechanismFloorHit->sourceModelIndex == 0);
    CHECK(movement.mechanismFloorHit->sourceObjectIndex == 55);
    CHECK(movement.finalPosition.x == doctest::Approx(5.0f));
    CHECK(movement.finalPosition.y == doctest::Approx(64.1f));
    CHECK(movement.finalPosition.z == doctest::Approx(5.0f));
    CHECK(movement.floorCandidateTriangleCount > 0);
    CHECK(movement.floorTestedTriangleCount > 0);
    CHECK(movement.mechanismCandidateCount == 1);
    CHECK(movement.mechanismTestedCount == 1);
    CHECK(movement.appliedDisplacement.y == doctest::Approx(-63.9f));
}

TEST_CASE("MM9 DAT party runtime carries party with moving mechanism floor support")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "platform.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "platform_0";
    mechanism.objectId = "platform_object_0";
    mechanism.sourceClass = "Elevator";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "platform_object_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "PlatformModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    REQUIRE(runtime.mechanismRuntime.stats.activeMechanismCount == 1);

    OpenYAMM::Game::Mm9DatDevStartPose startPose = {};
    startPose.position = {5.0f, 64.1f, 5.0f};
    startPose.snappedToFloor = true;
    OpenYAMM::Game::Mm9DatPartyRuntimeState state =
        OpenYAMM::Game::initializeMm9DatPartyRuntimeState(startPose);

    OpenYAMM::Game::Mm9DatPartyRuntimeMoveInput input = {};
    input.deltaSeconds = 0.0f;
    const OpenYAMM::Game::Mm9DatPartyRuntimeMoveResult initialMove =
        OpenYAMM::Game::moveMm9DatPartyRuntime(runtime, state, input);
    REQUIRE(initialMove.movement.mechanismFloorHit.has_value());
    REQUIRE(state.mechanismSupportHandle.has_value());
    CHECK(state.mechanismSupportProgress == doctest::Approx(0.0f));

    OpenYAMM::Game::commandMm9DatMechanism(
        runtime.mechanismRuntime,
        runtime.mechanismRuntime.mechanisms[0].handle,
        OpenYAMM::Game::Mm9DatMechanismCommand::Open);

    input.deltaSeconds = 0.5f;
    const OpenYAMM::Game::Mm9DatPartyRuntimeMoveResult carriedMove =
        OpenYAMM::Game::moveMm9DatPartyRuntime(runtime, state, input);

    REQUIRE(carriedMove.mechanismCarry.has_value());
    CHECK(carriedMove.mechanismCarry->applied);
    CHECK(carriedMove.mechanismCarry->previousProgress == doctest::Approx(0.0f));
    CHECK(carriedMove.mechanismCarry->newProgress == doctest::Approx(0.5f));
    CHECK(carriedMove.mechanismCarry->displacement.x == doctest::Approx(0.0f));
    CHECK(carriedMove.mechanismCarry->displacement.y == doctest::Approx(0.0f));
    CHECK(carriedMove.mechanismCarry->displacement.z == doctest::Approx(12.8f));
    CHECK(state.position.x == doctest::Approx(5.0f));
    CHECK(state.position.y == doctest::Approx(64.1f));
    CHECK(state.position.z == doctest::Approx(17.8f));
    REQUIRE(carriedMove.movement.mechanismFloorHit.has_value());
    REQUIRE(state.mechanismSupportHandle.has_value());
    CHECK(state.mechanismSupportProgress == doctest::Approx(0.5f));
}

TEST_CASE("MM9 DAT party runtime owns pose movement and use rays for native DAT worlds")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld(true);

    OpenYAMM::Game::Mm9DatDevStartPose startPose = {};
    startPose.position = {0.0f, 64.1f, 0.0f};
    startPose.snappedToFloor = true;
    OpenYAMM::Game::Mm9DatPartyRuntimeState partyState =
        OpenYAMM::Game::initializeMm9DatPartyRuntimeState(startPose);

    OpenYAMM::Game::Mm9DatPartyRuntimeMovementOptions movementOptions = {};
    movementOptions.walkSpeedLtPerSecond = 128.0f;
    movementOptions.radius = 8.0f;
    movementOptions.halfHeight = 64.0f;
    movementOptions.floorSnapDistance = 96.0f;

    OpenYAMM::Game::Mm9DatPartyRuntimeMoveInput moveInput = {};
    moveInput.forward = 1.0f;
    moveInput.deltaSeconds = 1.0f;

    const OpenYAMM::Game::Mm9DatPartyRuntimeMoveResult moveResult =
        OpenYAMM::Game::moveMm9DatPartyRuntime(
            runtime,
            partyState,
            moveInput,
            movementOptions);

    CHECK(moveResult.desiredDisplacement.x == doctest::Approx(128.0f));
    CHECK(moveResult.movement.blockedByWall);
    CHECK(moveResult.movement.onGround);
    CHECK(partyState.onGround);
    CHECK(partyState.position.x == doctest::Approx(moveResult.movement.finalPosition.x));

    runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    OpenYAMM::Game::Mm9EventTriggerOutput useTriggerOutput = {};
    useTriggerOutput.phase = "open";
    useTriggerOutput.slot = 0;
    useTriggerOutput.targetName = "DoorRelay";
    useTriggerOutput.messageName = "On";
    mechanism.triggerOutputs.push_back(useTriggerOutput);
    OpenYAMM::Game::Mm9EventMechanismSound useSound = {};
    useSound.phase = "open_start";
    useSound.sourceProperty = "OpenStartSound";
    useSound.soundName = "stone_door_open";
    useSound.authored = true;
    mechanism.sounds.push_back(useSound);
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);
    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.objectId = "door_0";
    object.sourceObjectIndex = 42;
    object.sourceClass = "Door";
    object.sourceName = "Door0";
    object.sourceModel = "DoorModel";
    object.scriptName = "Door0.scr";
    object.scriptParams = "param0,param1";
    object.x = 0.0f;
    object.y = 0.0f;
    object.z = 0.0f;
    object.radius = 16.0f;
    object.height = 64.0f;
    object.movement.moveToFloor = false;
    OpenYAMM::Game::Mm9ScriptedObject relayObject = {};
    relayObject.objectId = "relay_0";
    relayObject.sourceObjectIndex = 43;
    relayObject.sourceClass = "ScriptObject";
    relayObject.sourceName = "DoorRelay";
    relayObject.x = 0.0f;
    relayObject.y = 0.0f;
    relayObject.z = 0.0f;
    relayObject.radius = 16.0f;
    relayObject.height = 64.0f;
    relayObject.movement.moveToFloor = false;
    runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(
            {object, relayObject},
            runtime.collisionWorld,
            &runtime.mechanismRuntime);
    runtime.mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    REQUIRE(runtime.mechanismRuntime.mechanismIndexByObjectId.count("door_0") == 1);
    CHECK(runtime.mechanismRuntime.mechanismIndexByObjectId["door_0"] == 0);

    partyState.position = {-10.0f, 0.0f, 5.0f};
    partyState.yawRadians = 0.0f;
    partyState.pitchRadians = 0.0f;

    OpenYAMM::Game::Mm9DatPartyRuntimeUseOptions useOptions = {};
    useOptions.eyeHeight = 0.0f;
    useOptions.maxDistance = 64.0f;
    useOptions.includeWorld = false;
    useOptions.includeObjects = false;
    useOptions.command = OpenYAMM::Game::Mm9DatMechanismCommand::Open;

    const OpenYAMM::Game::Mm9DatWorldUseResult useResult =
        OpenYAMM::Game::useMm9DatPartyRuntime(runtime, partyState, useOptions);

    CHECK(useResult.picked);
    CHECK(useResult.activated);
    CHECK(useResult.hit.kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Mechanism);
    CHECK(runtime.mechanismRuntime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
}

TEST_CASE("MM9 DAT party runtime applies gravity and lands through DAT floor support")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();

    OpenYAMM::Game::Mm9DatDevStartPose startPose = {};
    startPose.position = {0.0f, 300.0f, 0.0f};
    startPose.snappedToFloor = false;
    OpenYAMM::Game::Mm9DatPartyRuntimeState partyState =
        OpenYAMM::Game::initializeMm9DatPartyRuntimeState(startPose);

    OpenYAMM::Game::Mm9DatPartyRuntimeMovementOptions movementOptions = {};
    movementOptions.halfHeight = 64.0f;
    movementOptions.floorSnapDistance = 8.0f;
    movementOptions.gravityLtPerSecondSquared = 100.0f;
    movementOptions.terminalFallSpeedLtPerSecond = 1000.0f;

    OpenYAMM::Game::Mm9DatPartyRuntimeMoveInput input = {};
    input.deltaSeconds = 0.1f;
    OpenYAMM::Game::Mm9DatPartyRuntimeMoveResult moveResult =
        OpenYAMM::Game::moveMm9DatPartyRuntime(
            runtime,
            partyState,
            input,
            movementOptions);

    CHECK(moveResult.gravityApplied);
    CHECK(moveResult.previousVerticalVelocityLtPerSecond == doctest::Approx(0.0f));
    CHECK(moveResult.newVerticalVelocityLtPerSecond == doctest::Approx(-10.0f));
    CHECK(moveResult.desiredDisplacement.y == doctest::Approx(-1.0f));
    CHECK(partyState.position.y == doctest::Approx(299.0f));
    CHECK_FALSE(partyState.onGround);

    partyState.position = {0.0f, 66.0f, 0.0f};
    partyState.onGround = false;
    partyState.verticalVelocityLtPerSecond = 0.0f;
    movementOptions.floorSnapDistance = 96.0f;
    moveResult = OpenYAMM::Game::moveMm9DatPartyRuntime(
        runtime,
        partyState,
        input,
        movementOptions);

    CHECK(moveResult.gravityApplied);
    CHECK(moveResult.movement.onGround);
    CHECK(moveResult.newVerticalVelocityLtPerSecond == doctest::Approx(0.0f));
    CHECK(partyState.onGround);
    CHECK(partyState.position.y == doctest::Approx(64.1f));
}

TEST_CASE("MM9 DAT party runtime snaps debug teleport to native floor support")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();

    OpenYAMM::Game::Mm9DatDevStartPose startPose = {};
    startPose.position = {0.0f, 64.1f, 0.0f};
    startPose.snappedToFloor = true;
    OpenYAMM::Game::Mm9DatPartyRuntimeState partyState =
        OpenYAMM::Game::initializeMm9DatPartyRuntimeState(startPose);

    const OpenYAMM::Game::Mm9DatPartyRuntimeTeleportResult result =
        OpenYAMM::Game::teleportMm9DatPartyRuntime(
            runtime,
            partyState,
            {10.0f, 500.0f, 20.0f},
            1.0f);

    CHECK(result.snappedToFloor);
    CHECK(result.onGround);
    CHECK(result.floorCandidateTriangleCount > 0);
    CHECK(result.floorTestedTriangleCount > 0);
    CHECK(result.requestedPosition.y == doctest::Approx(500.0f));
    CHECK(result.finalPosition.x == doctest::Approx(10.0f));
    CHECK(result.finalPosition.y == doctest::Approx(64.1f));
    CHECK(result.finalPosition.z == doctest::Approx(20.0f));
    CHECK(partyState.position.y == doctest::Approx(64.1f));
    CHECK(partyState.yawRadians == doctest::Approx(1.0f));
    CHECK(partyState.onGround);
}

TEST_CASE("MM9 DAT party runtime snaps debug teleport to transformed mechanism floor support")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "platform.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "platform_0";
    mechanism.objectId = "platform_object_0";
    mechanism.sourceObjectIndex = 55;
    mechanism.sourceClass = "Elevator";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "platform_object_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "PlatformModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);

    OpenYAMM::Game::Mm9DatDevStartPose startPose = {};
    startPose.position = {0.0f, 64.1f, 0.0f};
    startPose.snappedToFloor = true;
    OpenYAMM::Game::Mm9DatPartyRuntimeState partyState =
        OpenYAMM::Game::initializeMm9DatPartyRuntimeState(startPose);

    const OpenYAMM::Game::Mm9DatPartyRuntimeTeleportResult result =
        OpenYAMM::Game::teleportMm9DatPartyRuntime(
            runtime,
            partyState,
            {5.0f, 500.0f, 5.0f},
            0.25f);

    CHECK(result.snappedToFloor);
    CHECK(result.onGround);
    REQUIRE(result.mechanismFloorHit.has_value());
    CHECK(result.mechanismFloorHit->mechanismId == "platform_0");
    CHECK(result.mechanismCandidateCount == 1);
    CHECK(result.mechanismTestedCount == 1);
    CHECK(result.mechanismCandidateTriangleCount > 0);
    CHECK(result.mechanismTestedTriangleCount > 0);
    CHECK(result.finalPosition.x == doctest::Approx(5.0f));
    CHECK(result.finalPosition.y == doctest::Approx(64.1f));
    CHECK(result.finalPosition.z == doctest::Approx(5.0f));
    REQUIRE(partyState.mechanismSupportHandle.has_value());
    CHECK(*partyState.mechanismSupportHandle == runtime.mechanismRuntime.mechanisms[0].handle);
    CHECK(partyState.mechanismSupportProgress == doctest::Approx(0.0f));
}

TEST_CASE("MM9 DAT scene runtime exposes native DAT movement through gameplay world interface")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld(true);
    entry.startPose.position = {0.0f, 64.1f, 0.0f};
    entry.startPose.snappedToFloor = true;

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party,
        9.0f * 60.0f);

    CHECK(sceneRuntime.kind() == OpenYAMM::Game::SceneKind::Outdoor);
    CHECK(sceneRuntime.currentMapFileName() == "test.odm");
    CHECK(sceneRuntime.worldRuntime().currentMapWorldId() == "mm9");
    CHECK(sceneRuntime.worldRuntime().partyX() == doctest::Approx(0.0f));
    CHECK(sceneRuntime.worldRuntime().partyFootZ() == doctest::Approx(64.1f));

    OpenYAMM::Game::GameplayInputFrame input = {};
    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;

    sceneRuntime.worldRuntime().updateWorldMovement(input, 1.0f, true);

    REQUIRE(sceneRuntime.worldRuntime().lastMoveResult().has_value());
    CHECK(sceneRuntime.worldRuntime().lastMoveResult()->movement.blockedByWall);
    CHECK(sceneRuntime.worldRuntime().partyX() > 0.0f);
    CHECK(sceneRuntime.worldRuntime().partyFootZ() == doctest::Approx(64.1f));

    CHECK(sceneRuntime.worldRuntime().teleportPartyTo(10.0f, 20.0f, 30.0f, 90));
    CHECK(sceneRuntime.worldRuntime().partyX() == doctest::Approx(10.0f));
    CHECK(sceneRuntime.worldRuntime().partyY() == doctest::Approx(20.0f));
    CHECK(sceneRuntime.worldRuntime().partyFootZ() == doctest::Approx(64.1f));
    CHECK(sceneRuntime.worldRuntime().gameplayCameraYawRadians() == doctest::Approx(1.5707963268f));

    OpenYAMM::Game::GameplayInputFrame strafeInput = {};
    strafeInput.modernControls = true;
    strafeInput.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Left)].held = true;
    sceneRuntime.worldRuntime().updateWorldMovement(strafeInput, 0.1f, true);
    CHECK(sceneRuntime.worldRuntime().partyX() > 10.0f);
    CHECK(sceneRuntime.worldRuntime().gameplayCameraYawRadians() == doctest::Approx(1.5707963268f));

    OpenYAMM::Game::GameplayInputFrame turnInput = {};
    turnInput.modernControls = false;
    turnInput.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Left)].held = true;
    turnInput.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::LookUp)].held = true;
    sceneRuntime.worldRuntime().updateWorldMovement(turnInput, 0.1f, true);
    CHECK(sceneRuntime.worldRuntime().gameplayCameraYawRadians() > 1.5707963268f);
    CHECK(sceneRuntime.worldRuntime().gameplayCameraPitchRadians() > 0.0f);

    const float beforeJumpFootZ = sceneRuntime.worldRuntime().partyFootZ();
    sceneRuntime.worldRuntime().requestPartyJump(300.0f, 1.0f);
    OpenYAMM::Game::GameplayInputFrame airborneInput = {};
    sceneRuntime.worldRuntime().updateWorldMovement(airborneInput, 0.1f, true);
    REQUIRE(sceneRuntime.worldRuntime().lastMoveResult().has_value());
    CHECK(sceneRuntime.worldRuntime().lastMoveResult()->gravityApplied);
    CHECK(sceneRuntime.worldRuntime().partyFootZ() > beforeJumpFootZ);
    CHECK_FALSE(sceneRuntime.worldRuntime().partyRuntimeState().onGround);
}

TEST_CASE("MM9 DAT scene runtime exposes DAT object actors through shared actor queries")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld();
    entry.startPose.position = {0.0f, 64.1f, 0.0f};

    OpenYAMM::Game::Mm9ScriptedObject actor = scriptedObject(10, "Dragon", false, true);
    actor.sourceName = "Dragon0";
    actor.visualId = "dragon";
    actor.x = 10.0f;
    actor.y = 20.0f;
    actor.z = 30.0f;
    actor.radius = 16.0f;
    actor.height = 96.0f;
    OpenYAMM::Game::Mm9ScriptedObject farActor = scriptedObject(11, "Dragon", false, true);
    farActor.sourceName = "Dragon1";
    farActor.visualId = "dragon";
    farActor.x = 2048.0f;
    farActor.y = 20.0f;
    farActor.z = 2048.0f;
    farActor.radius = 16.0f;
    farActor.height = 96.0f;
    entry.level.runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry({actor, farActor}, entry.level.runtime.collisionWorld);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9ScriptRuntimeState scriptState = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party,
        0.0f,
        &scriptState);

    CHECK(sceneRuntime.worldRuntime().mapActorCount() == 2);
    CHECK(sceneRuntime.worldRuntime().datRuntime().objectRegistry.stats.actorCellCount > 0);
    CHECK(sceneRuntime.worldRuntime().datRuntime().objectRegistry.stats.actorCellObjectRefs >= 2);

    OpenYAMM::Game::GameplayRuntimeActorState actorState = {};
    REQUIRE(sceneRuntime.worldRuntime().actorRuntimeState(0, actorState));
    CHECK(actorState.preciseX == doctest::Approx(10.0f));
    CHECK(actorState.preciseY == doctest::Approx(30.0f));
    CHECK(actorState.preciseZ == doctest::Approx(20.0f));
    CHECK(actorState.radius == 16);
    CHECK(actorState.height == 96);
    CHECK_FALSE(actorState.isInvisible);

    OpenYAMM::Game::GameplayActorInspectState inspectState = {};
    REQUIRE(sceneRuntime.worldRuntime().actorInspectState(0, 0, inspectState));
    CHECK(inspectState.displayName == "Dragon0");
    CHECK(inspectState.previewTextureName == "dragon");

    const std::vector<size_t> nearbyActors =
        sceneRuntime.worldRuntime().collectMapActorIndicesWithinRadius(
            10.0f,
            30.0f,
            20.0f,
            128.0f,
            false,
            10.0f,
            30.0f,
            20.0f);
    REQUIRE(nearbyActors.size() == 1);
    CHECK(nearbyActors[0] == 0);

    const std::vector<size_t> farActors =
        sceneRuntime.worldRuntime().collectMapActorIndicesWithinRadius(
            2048.0f,
            2048.0f,
            20.0f,
            128.0f,
            false,
            2048.0f,
            2048.0f,
            20.0f);
    REQUIRE(farActors.size() == 1);
    CHECK(farActors[0] == 1);
}

TEST_CASE("MM9 DAT actor line of sight queries include transformed mechanism collision")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld();
    entry.level.runtime.renderMesh.triangles.push_back(wallTriangle());
    entry.startPose.position = {0.0f, 64.1f, 0.0f};

    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    OpenYAMM::Game::Mm9EventsData events = {};
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 8;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    entry.level.runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, entry.level.runtime.renderMesh);
    entry.level.runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(entry.level.runtime.mechanismRuntime);
    entry.level.runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(
            entry.level.runtime.renderMesh,
            entry.level.runtime.mechanismRuntime);

    OpenYAMM::Game::Mm9ScriptedObject actor = scriptedObject(10, "Dragon", false, true);
    actor.sourceName = "Dragon0";
    actor.x = 128.0f;
    actor.y = 0.0f;
    actor.z = 0.0f;
    actor.radius = 16.0f;
    actor.height = 96.0f;
    entry.level.runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(
            {actor},
            entry.level.runtime.collisionWorld,
            &entry.level.runtime.mechanismRuntime);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party);

    const std::vector<size_t> withoutLineOfSight =
        sceneRuntime.worldRuntime().collectMapActorIndicesWithinRadius(
            128.0f,
            0.0f,
            0.0f,
            256.0f,
            false,
            0.0f,
            0.0f,
            0.0f);
    REQUIRE(withoutLineOfSight.size() == 1);
    CHECK(withoutLineOfSight[0] == 0);

    const std::vector<size_t> withLineOfSight =
        sceneRuntime.worldRuntime().collectMapActorIndicesWithinRadius(
            128.0f,
            0.0f,
            0.0f,
            256.0f,
            true,
            0.0f,
            0.0f,
            0.0f);
    CHECK(withLineOfSight.empty());
}

TEST_CASE("MM9 DAT scene runtime maps picked actor objects to shared actor hits")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld();
    entry.startPose.position = {-10.0f, 0.0f, 5.0f};

    OpenYAMM::Game::Mm9ScriptedObject actor = scriptedObject(10, "Dragon", false, true);
    actor.sourceName = "Dragon0";
    actor.x = 30.0f;
    actor.y = 32.0f;
    actor.z = 5.0f;
    actor.radius = 32.0f;
    actor.height = 128.0f;
    entry.level.runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry({actor}, entry.level.runtime.collisionWorld);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9ScriptRuntimeState scriptState = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party,
        0.0f,
        &scriptState);

    OpenYAMM::Game::GameplayWorldPickRequestInput requestInput = {};
    requestInput.includeRay = true;
    OpenYAMM::Game::GameplayWorldPickRequest request =
        sceneRuntime.worldRuntime().buildWorldPickRequest(requestInput);
    OpenYAMM::Game::GameplayWorldHit hit =
        sceneRuntime.worldRuntime().pickKeyboardInteractionTarget(request);

    REQUIRE(hit.hasHit);
    CHECK(hit.kind == OpenYAMM::Game::GameplayWorldHitKind::Actor);
    REQUIRE(hit.actor.has_value());
    CHECK(hit.actor->actorIndex == 0);
    CHECK(hit.actor->displayName == "Dragon0");
    CHECK(hit.actor->distance == doctest::Approx(8.0f));
    CHECK_FALSE(sceneRuntime.worldRuntime().canActivateWorldHit(
        hit,
        OpenYAMM::Game::GameplayInteractionMethod::Keyboard));
}

TEST_CASE("MM9 DAT scene runtime exposes native DAT mechanism picking through gameplay interaction")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld();
    entry.level.runtime.renderMesh.triangles.push_back(wallTriangle());
    entry.startPose.position = {-10.0f, 0.0f, 5.0f};
    entry.startPose.snappedToFloor = true;

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 8;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    entry.level.runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, entry.level.runtime.renderMesh);
    entry.level.runtime.mechanismRuntime.mechanisms[0].handle = 77;
    entry.level.runtime.mechanismRuntime.mechanismIndexByHandle.clear();
    entry.level.runtime.mechanismRuntime.mechanismIndexByHandle.emplace(77, 0);
    entry.level.runtime.mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(
            entry.level.runtime.renderMesh,
            entry.level.runtime.mechanismRuntime);
    entry.level.runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(entry.level.runtime.mechanismRuntime);
    entry.level.runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(
            entry.level.runtime.renderMesh,
            entry.level.runtime.mechanismRuntime);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9ScriptRuntimeState scriptState = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party,
        0.0f,
        &scriptState);

    OpenYAMM::Game::GameplayWorldPickRequestInput requestInput = {};
    requestInput.includeRay = true;
    requestInput.screenWidth = 1280;
    requestInput.screenHeight = 720;
    OpenYAMM::Game::GameplayWorldPickRequest request =
        sceneRuntime.worldRuntime().buildWorldPickRequest(requestInput);

    OpenYAMM::Game::GameplayWorldHit hit =
        sceneRuntime.worldRuntime().pickKeyboardInteractionTarget(request);

    REQUIRE(hit.hasHit);
    REQUIRE(hit.eventTarget.has_value());
    CHECK(hit.kind == OpenYAMM::Game::GameplayWorldHitKind::EventTarget);
    CHECK(hit.eventTarget->targetKind == OpenYAMM::Game::GameplayWorldEventTargetKind::Mechanism);
    CHECK(hit.eventTarget->targetIndex == 77);
    CHECK(hit.eventTarget->name == "Door0");
    REQUIRE(hit.eventTarget->contextActionMetadata.has_value());
    CHECK(hit.eventTarget->contextActionMetadata->kind == "use_switch");
    CHECK(hit.eventTarget->contextActionMetadata->source == "mm9_dat");
    CHECK(hit.eventTarget->contextActionMetadata->mm9ObjectId == "door_0");
    REQUIRE(hit.eventTarget->contextActionMetadata->mm9SourceObjectIndex.has_value());
    CHECK(*hit.eventTarget->contextActionMetadata->mm9SourceObjectIndex == 42);
    CHECK(sceneRuntime.worldRuntime().canActivateWorldHit(
        hit,
        OpenYAMM::Game::GameplayInteractionMethod::Keyboard));

    CHECK(sceneRuntime.worldRuntime().activateWorldHit(hit));
    REQUIRE(sceneRuntime.worldRuntime().lastUseResult().has_value());
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activated);
    CHECK(sceneRuntime.worldRuntime().datRuntime().mechanismRuntime.mechanisms[0].state
        == OpenYAMM::Game::Mm9DatMechanismState::Opening);

    OpenYAMM::Game::GameplayWorldHoverRequest hoverRequest = {};
    hoverRequest.primaryPickRequest = request;
    hoverRequest.updateTickNanoseconds = 1234;
    const OpenYAMM::Game::GameplayHoverStatusPayload hover =
        sceneRuntime.worldRuntime().refreshWorldHover(hoverRequest);
    CHECK(hover.worldHit.hasHit);
    CHECK(hover.eventTargetStatusText == "Door0");
    CHECK(sceneRuntime.worldRuntime().worldHoverCacheState().hasCachedHover);
    CHECK(sceneRuntime.worldRuntime().worldHoverCacheState().lastUpdateNanoseconds == 1234);
}

TEST_CASE("MM9 DAT scene runtime routes picked objects to linked mechanisms")
{
    OpenYAMM::Game::Mm9DatRuntimeDevEntryResult entry = {};
    entry.level.metadata.mapId = "test";
    entry.level.runtime.mapId = "test";
    entry.level.runtime.collisionWorld = syntheticCollisionWorld();
    entry.level.runtime.renderMesh.triangles.push_back(wallTriangle());
    entry.startPose.position = {-10.0f, 0.0f, 5.0f};

    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.objectId = "door_0";
    object.sourceObjectIndex = 42;
    object.sourceClass = "Lever";
    object.sourceName = "Lever0";
    object.scriptName = "Lever0.scr";
    object.scriptParams = "toggle_target=door_0";
    object.x = 30.0f;
    object.y = 32.0f;
    object.z = 5.0f;
    object.radius = 32.0f;
    object.height = 128.0f;
    object.movement.moveToFloor = false;
    OpenYAMM::Game::Mm9ScriptedObject relayObject = {};
    relayObject.objectId = "relay_0";
    relayObject.sourceObjectIndex = 43;
    relayObject.sourceClass = "ScriptObject";
    relayObject.sourceName = "ScriptRelay";
    relayObject.x = 60.0f;
    relayObject.y = 32.0f;
    relayObject.z = 5.0f;
    relayObject.radius = 16.0f;
    relayObject.height = 64.0f;
    relayObject.movement.moveToFloor = false;

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    OpenYAMM::Game::Mm9EventTriggerOutput output = {};
    output.phase = "open";
    output.slot = 1;
    output.targetName = "ScriptRelay";
    output.messageName = "Trigger";
    mechanism.triggerOutputs.push_back(output);
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 8;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    entry.level.runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, entry.level.runtime.renderMesh);
    entry.level.runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(
            {object, relayObject},
            entry.level.runtime.collisionWorld,
            &entry.level.runtime.mechanismRuntime);
    entry.level.runtime.objectRegistry.objects[0].handle = 99;
    entry.level.runtime.objectRegistry.objectIndexByHandle.clear();
    entry.level.runtime.objectRegistry.objectIndexByHandle.emplace(99, 0);
    entry.level.runtime.objectRegistry.objectIndexByHandle.emplace(
        entry.level.runtime.objectRegistry.objects[1].handle,
        1);
    entry.level.runtime.mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(
            entry.level.runtime.renderMesh,
            entry.level.runtime.mechanismRuntime);
    entry.level.runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(entry.level.runtime.mechanismRuntime);
    entry.level.runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(
            entry.level.runtime.renderMesh,
            entry.level.runtime.mechanismRuntime);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9ScriptRuntimeState scriptState = {};
    OpenYAMM::Game::Mm9DatSceneRuntime sceneRuntime(
        "test.odm",
        std::move(entry),
        party,
        0.0f,
        &scriptState);

    OpenYAMM::Game::GameplayWorldPickRequestInput requestInput = {};
    requestInput.includeRay = true;
    OpenYAMM::Game::GameplayWorldPickRequest request =
        sceneRuntime.worldRuntime().buildWorldPickRequest(requestInput);
    OpenYAMM::Game::GameplayWorldHit hit =
        sceneRuntime.worldRuntime().pickKeyboardInteractionTarget(request);

    REQUIRE(hit.hasHit);
    REQUIRE(hit.eventTarget.has_value());
    CHECK(hit.eventTarget->targetKind == OpenYAMM::Game::GameplayWorldEventTargetKind::Object);
    CHECK(hit.eventTarget->targetIndex == 99);
    CHECK(hit.eventTarget->name == "Lever0");
    REQUIRE(hit.eventTarget->contextActionMetadata.has_value());
    CHECK(hit.eventTarget->contextActionMetadata->mm9SourceClass == "Lever");
    CHECK(sceneRuntime.worldRuntime().canActivateWorldHit(
        hit,
        OpenYAMM::Game::GameplayInteractionMethod::Keyboard));

    CHECK(sceneRuntime.worldRuntime().activateWorldHit(hit));
    REQUIRE(sceneRuntime.worldRuntime().lastUseResult().has_value());
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->hit.kind
        == OpenYAMM::Game::Mm9DatWorldPickHitKind::Object);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.hasObject);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.hasMechanism);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.objectSourceClass == "Lever");
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.objectScriptName == "Lever0.scr");
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.mechanismKind == "linear_door");
    REQUIRE(sceneRuntime.worldRuntime().lastUseResult()->activation.triggerOutputs.size() == 1);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->activation.triggerOutputs[0].targetName == "ScriptRelay");
    REQUIRE(sceneRuntime.worldRuntime().lastUseResult()->triggerDispatches.size() == 1);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->triggerDispatches[0].resolvedTarget);
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->triggerDispatches[0].targetObjectId == "relay_0");
    CHECK(sceneRuntime.worldRuntime().lastUseResult()->triggerDispatches[0].messageName == "Trigger");
    REQUIRE(scriptState.triggerDispatches.size() == 1);
    CHECK(scriptState.triggerDispatches[0].mapId == "test");
    CHECK(scriptState.triggerDispatches[0].objectIndex == 42);
    CHECK(scriptState.triggerDispatches[0].scriptSource == "Lever0.scr");
    CHECK(scriptState.triggerDispatches[0].targetHandle == "relay_0");
    CHECK(scriptState.triggerDispatches[0].message == "Trigger");
    CHECK(sceneRuntime.worldRuntime().datRuntime().mechanismRuntime.mechanisms[0].state
        == OpenYAMM::Game::Mm9DatMechanismState::Opening);
}

TEST_CASE("MM9 DAT world picking returns source world triangle ids")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld(true);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = {0.0f, 64.0f, 0.0f};
    ray.direction = {1.0f, 0.0f, 0.0f};

    OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
    options.includeObjects = false;
    options.includeMechanisms = false;
    options.worldChannelMask = OpenYAMM::Game::Mm9DatPhysicsQueryChannelPhysics;
    options.maxDistance = 128.0f;

    const std::optional<OpenYAMM::Game::Mm9DatWorldPickHit> hit =
        OpenYAMM::Game::pickMm9DatWorldRuntime(runtime, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::World);
    CHECK(hit->distance == doctest::Approx(64.0f));
    CHECK(hit->sourceModelIndex == 8);
    CHECK(hit->sourcePolyIndex == 12);
    CHECK(hit->sourceSurfaceIndex == 14);
    CHECK(hit->sourceModelName == "PhysicsBSP");
    CHECK(hit->candidateTriangleCount > 0);
    CHECK(hit->testedTriangleCount > 0);
}

TEST_CASE("MM9 DAT object registry applies LithTech-style MoveToFloor as a one-shot policy")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld collisionWorld = syntheticCollisionWorld();
    std::vector<OpenYAMM::Game::Mm9ScriptedObject> objects;
    objects.push_back(scriptedObject(0, "Prop", true, false));
    objects.push_back(scriptedObject(1, "Prop", false, false));
    objects.push_back(scriptedObject(2, "Dragon", true, true));

    const OpenYAMM::Game::Mm9DatObjectRegistry registry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(objects, collisionWorld);

    REQUIRE(registry.objects.size() == 3);
    CHECK(registry.objects[0].placementStatus == OpenYAMM::Game::Mm9DatObjectPlacementStatus::SnappedToFloor);
    CHECK(registry.objects[0].position.y == doctest::Approx(64.1f));
    CHECK(registry.objects[1].placementStatus == OpenYAMM::Game::Mm9DatObjectPlacementStatus::Authored);
    CHECK(registry.objects[1].position.y == doctest::Approx(512.0f));
    CHECK(registry.objects[2].placementStatus == OpenYAMM::Game::Mm9DatObjectPlacementStatus::PolicySkipped);
    CHECK(registry.objects[2].position.y == doctest::Approx(512.0f));
    CHECK(registry.stats.snappedToFloorCount == 1);
    CHECK(registry.stats.policySkippedMoveToFloorCount == 1);
    CHECK(registry.stats.pickableCellCount > 0);
    CHECK(registry.stats.pickableCellObjectRefs > 0);
}

TEST_CASE("MM9 DAT object registry builds typed membership views for runtime systems")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld collisionWorld = syntheticCollisionWorld();
    std::vector<OpenYAMM::Game::Mm9ScriptedObject> objects;

    OpenYAMM::Game::Mm9ScriptedObject prop = scriptedObject(0, "Prop", false, false);
    prop.sourceModel = "crate.ltb";
    prop.visualId = "crate";
    prop.scriptName = "UseCrate";
    objects.push_back(prop);

    OpenYAMM::Game::Mm9ScriptedObject actor = scriptedObject(1, "Dragon", false, true);
    actor.sourceModel = "dragon.ltb";
    objects.push_back(actor);

    OpenYAMM::Game::Mm9ScriptedObject trigger = scriptedObject(2, "TriggerVolume", false, false);
    trigger.needsTick = true;
    objects.push_back(trigger);

    OpenYAMM::Game::Mm9ScriptedObject light = scriptedObject(3, "StaticLight", false, false);
    light.sourceName = "TorchLight0";
    objects.push_back(light);

    OpenYAMM::Game::Mm9ScriptedObject mechanismObject = scriptedObject(4, "Switch", false, false);
    mechanismObject.objectId = "door_0";
    mechanismObject.sourceModel = "switch.ltb";
    objects.push_back(mechanismObject);

    OpenYAMM::Game::Mm9DatMechanismRuntime mechanismRuntime = {};
    OpenYAMM::Game::Mm9DatMechanismInstance mechanism = {};
    mechanism.objectId = "door_0";
    mechanismRuntime.mechanisms.push_back(mechanism);

    const OpenYAMM::Game::Mm9DatObjectRegistry registry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(objects, collisionWorld, &mechanismRuntime);

    CHECK(registry.stats.objectCount == 5);
    CHECK(registry.stats.renderableObjectCount == 3);
    CHECK(registry.renderableObjectIndices.size() == registry.stats.renderableObjectCount);
    CHECK(registry.stats.collidableObjectCount == 5);
    CHECK(registry.collidableObjectIndices.size() == registry.stats.collidableObjectCount);
    CHECK(registry.stats.rayHitObjectCount == 5);
    CHECK(registry.rayHitObjectIndices.size() == registry.stats.rayHitObjectCount);
    CHECK(registry.stats.interactableObjectCount == 5);
    CHECK(registry.interactableObjectIndices.size() == registry.stats.interactableObjectCount);
    CHECK(registry.stats.actorObjectCount == 1);
    REQUIRE(registry.actorObjectIndices.size() == 1);
    CHECK(registry.objects[registry.actorObjectIndices[0]].sourceClass == "Dragon");
    CHECK(registry.stats.actorCellCount > 0);
    CHECK(registry.stats.actorCellObjectRefs > 0);
    CHECK(registry.stats.maxActorCellObjectRefs > 0);
    REQUIRE(registry.actorIndexByObjectIndex.size() == registry.objects.size());
    CHECK(registry.actorIndexByObjectIndex[1] == 0);
    CHECK(registry.stats.propObjectCount == 1);
    CHECK(registry.stats.triggerObjectCount == 1);
    CHECK(registry.stats.lightObjectCount == 1);
    CHECK(registry.stats.mechanismObjectCount == 1);
    REQUIRE(registry.mechanismObjectIndices.size() == 1);
    CHECK(registry.objects[registry.mechanismObjectIndices[0]].objectId == "door_0");
    CHECK(registry.stats.tickingObjectCount == 1);
    REQUIRE(registry.tickingObjectIndices.size() == 1);
    CHECK(registry.objects[registry.tickingObjectIndices[0]].sourceClass == "TriggerVolume");
}

TEST_CASE("MM9 DAT object presentation world is built from load-time registry views")
{
    const OpenYAMM::Game::Mm9DatCollisionWorld collisionWorld = syntheticCollisionWorld();
    std::vector<OpenYAMM::Game::Mm9ScriptedObject> objects;

    OpenYAMM::Game::Mm9ScriptedObject prop = scriptedObject(0, "Prop", false, false);
    prop.sourceModel = "crate.ltb";
    prop.modelAsset = "models/crate.glb";
    objects.push_back(prop);

    OpenYAMM::Game::Mm9ScriptedObject actor = scriptedObject(1, "Dragon", false, true);
    actor.sourceModel = "dragon.ltb";
    actor.modelAsset = "models/dragon.glb";
    objects.push_back(actor);

    OpenYAMM::Game::Mm9ScriptedObject trigger = scriptedObject(2, "TriggerVolume", false, false);
    objects.push_back(trigger);

    OpenYAMM::Game::Mm9ScriptedObject mechanismObject = scriptedObject(3, "Switch", false, false);
    mechanismObject.objectId = "door_0";
    mechanismObject.sourceModel = "switch.ltb";
    objects.push_back(mechanismObject);

    OpenYAMM::Game::Mm9DatMechanismRuntime mechanismRuntime = {};
    OpenYAMM::Game::Mm9DatMechanismInstance mechanism = {};
    mechanism.objectId = "door_0";
    mechanismRuntime.mechanisms.push_back(mechanism);

    const OpenYAMM::Game::Mm9DatObjectRegistry registry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(objects, collisionWorld, &mechanismRuntime);
    const OpenYAMM::Game::Mm9DatObjectPresentationWorld presentation =
        OpenYAMM::Game::buildMm9DatObjectPresentationWorld(registry);

    CHECK(presentation.stats.instanceCount == registry.stats.renderableObjectCount);
    REQUIRE(presentation.instances.size() == 3);
    CHECK(presentation.stats.actorInstanceCount == 1);
    CHECK(presentation.stats.propInstanceCount == 1);
    CHECK(presentation.stats.mechanismInstanceCount == 1);
    CHECK(presentation.stats.modelAssetInstanceCount == 2);
    CHECK(presentation.stats.sourceModelWithoutModelAssetCount == 1);
    CHECK(presentation.instances[0].objectHandle == registry.objects[registry.renderableObjectIndices[0]].handle);
    CHECK(presentation.instances[0].kind == OpenYAMM::Game::Mm9DatObjectPresentationKind::Prop);
    CHECK(presentation.instances[1].kind == OpenYAMM::Game::Mm9DatObjectPresentationKind::Actor);
    CHECK(presentation.instances[2].kind == OpenYAMM::Game::Mm9DatObjectPresentationKind::Mechanism);
}

TEST_CASE("MM9 DAT world picking returns stable object handles through the object cell index")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    std::vector<OpenYAMM::Game::Mm9ScriptedObject> objects;
    objects.push_back(scriptedObjectAt(10, {64.0f, 0.0f, 0.0f}));
    runtime.objectRegistry = OpenYAMM::Game::buildMm9DatObjectRegistry(objects, runtime.collisionWorld);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = {0.0f, 64.0f, 0.0f};
    ray.direction = {1.0f, 0.0f, 0.0f};

    OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
    options.includeWorld = false;
    options.includeMechanisms = false;
    options.maxDistance = 128.0f;

    const std::optional<OpenYAMM::Game::Mm9DatWorldPickHit> hit =
        OpenYAMM::Game::pickMm9DatWorldRuntime(runtime, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Object);
    CHECK(hit->objectHandle == 1);
    CHECK(hit->objectId == "object_10");
    CHECK(hit->sourceObjectIndex == 10);
    CHECK(hit->distance == doctest::Approx(48.0f));
    CHECK(hit->candidateObjectCount > 0);
    CHECK(hit->testedObjectCount > 0);
    CHECK(runtime.objectRegistry.stats.pickableCellCount > 0);
}

TEST_CASE("MM9 DAT mechanism runtime resolves event bindings into active source-model motion")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "RotatingDoor";
    mechanism.sourceName = "Door0";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    mechanism.linear.hasOpenSpeed = true;
    mechanism.linear.openSpeedLtPerSecond = 20.0f;
    mechanism.linear.hasCloseSpeed = true;
    mechanism.linear.closeSpeedLtPerSecond = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    binding.sourceObjectIndex = 42;
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.targetKind = "model_instance";
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    const OpenYAMM::Game::Mm9DatMechanismRuntime runtime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, mesh);

    REQUIRE(runtime.mechanisms.size() == 1);
    CHECK(runtime.stats.mechanismCount == 1);
    CHECK(runtime.stats.activeMechanismCount == 1);
    CHECK(runtime.stats.inertMechanismCount == 0);
    CHECK(runtime.stats.linearMotionCount == 1);
    CHECK(runtime.mechanisms[0].active);
    CHECK(runtime.mechanisms[0].sourceModelIndex == 0);
    CHECK(runtime.mechanisms[0].sourceModelName == "DoorModel");
    CHECK(runtime.mechanisms[0].motion.hasLinearMotion);
    CHECK(runtime.mechanisms[0].boundsChangeKnown);
    CHECK(runtime.mechanisms[0].boundsChanged);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closed);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(0.0f));
    CHECK(runtime.mechanisms[0].openingDurationSeconds == doctest::Approx(0.5f));
    CHECK(runtime.mechanisms[0].closingDurationSeconds == doctest::Approx(1.0f));
}

TEST_CASE("MM9 DAT mechanism source models move out of static render partitions")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));
    mesh.triangles.push_back(visualTriangle(1, "stone.dtx", 64.0f));

    OpenYAMM::Game::Mm9DatRenderFilterResult filters = {};
    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        OpenYAMM::Game::Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = mesh.triangles[triangleIndex].sourceModelIndex;
        entry.sourcePolyIndex = mesh.triangles[triangleIndex].sourcePolyIndex;
        entry.sourceSurfaceIndex = mesh.triangles[triangleIndex].sourceSurfaceIndex;
        entry.flags = OpenYAMM::Game::Mm9DatRenderFilterVisual;
        filters.entries.push_back(entry);
    }

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceClass = "Door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    OpenYAMM::Game::Mm9DatMechanismRuntime mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, mesh);
    REQUIRE(mechanismRuntime.stats.activeMechanismCount == 1);

    OpenYAMM::Game::Mm9DatRenderWorld staticRenderWorld =
        OpenYAMM::Game::buildMm9DatRenderWorld(mesh, filters, {}, {0});
    OpenYAMM::Game::Mm9DatMechanismRenderWorld mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(mesh, mechanismRuntime);
    OpenYAMM::Game::Mm9DatPreparedRenderWorld preparedRenderWorld =
        OpenYAMM::Game::buildMm9DatPreparedRenderWorld(
            mesh,
            staticRenderWorld,
            mechanismRenderWorld,
            filters);

    REQUIRE(staticRenderWorld.partitions.size() == 1);
    CHECK(staticRenderWorld.partitions[0].sourceModelIndex == 1);
    CHECK(staticRenderWorld.stats.dynamicMechanismSkippedTriangleCount == 1);
    REQUIRE(mechanismRenderWorld.batches.size() == 1);
    CHECK(mechanismRenderWorld.batches[0].mechanismHandle == mechanismRuntime.mechanisms[0].handle);
    CHECK(mechanismRenderWorld.batches[0].sourceModelIndex == 0);
    CHECK(mechanismRenderWorld.batches[0].triangleIndices.size() == 1);
    CHECK(preparedRenderWorld.stats.staticSectionCount == 1);
    CHECK(preparedRenderWorld.stats.dynamicSectionCount == 1);
    CHECK(preparedRenderWorld.stats.staticTriangleCount == 1);
    CHECK(preparedRenderWorld.stats.dynamicTriangleCount == 1);
    REQUIRE(preparedRenderWorld.sections.size() == 2);
    REQUIRE(preparedRenderWorld.sections[1].dynamic);
    CHECK(preparedRenderWorld.sections[1].mechanismHandle == mechanismRuntime.mechanisms[0].handle);
    CHECK(preparedRenderWorld.sections[1].sourceTriangleIndices.size() == 1);
    CHECK(preparedRenderWorld.vertices[preparedRenderWorld.sections[1].vertexStart].z == doctest::Approx(0.0f));

    OpenYAMM::Game::commandMm9DatMechanism(
        mechanismRuntime,
        mechanismRuntime.mechanisms[0].handle,
        OpenYAMM::Game::Mm9DatMechanismCommand::Open);
    OpenYAMM::Game::updateMm9DatMechanisms(mechanismRuntime, 0.5f);
    OpenYAMM::Game::updateMm9DatMechanismRenderWorldTransforms(mechanismRenderWorld, mechanismRuntime);
    OpenYAMM::Game::updateMm9DatPreparedMechanismRenderWorld(
        preparedRenderWorld,
        mesh,
        mechanismRenderWorld);

    CHECK(mechanismRenderWorld.batches[0].motion.progress == doctest::Approx(0.5f));
    CHECK(preparedRenderWorld.vertices[preparedRenderWorld.sections[1].vertexStart].z == doctest::Approx(12.8f));
    CHECK(preparedRenderWorld.sections[1].bounds.min.z == doctest::Approx(12.8f));
}

TEST_CASE("MM9 DAT mechanism point transforms share render triangle transform authority")
{
    OpenYAMM::Game::Mm9DatRenderTriangle triangle = visualTriangle(0, "platform.dtx", 0.0f);
    OpenYAMM::Game::Mm9DatMechanismPreviewMotion motion = {};
    motion.sourceModelIndex = 0;
    motion.progress = 0.5f;
    motion.hasLinearMotion = true;
    motion.moveDirLt = {0.0f, 1.0f, 0.0f};
    motion.moveDistLt = 10.0f;
    motion.hasRotationMotion = true;
    motion.rotationPointLt = {0.0f, 0.0f, 0.0f};
    motion.rotationAnglesDeg = {0.0f, 0.0f, 90.0f};

    const OpenYAMM::Game::Mm9DatVec3 sourcePoint = {
        triangle.vertices[0].x,
        triangle.vertices[0].y,
        triangle.vertices[0].z,
    };
    const OpenYAMM::Game::Mm9DatRenderTriangle transformedTriangle =
        OpenYAMM::Game::transformMm9DatMechanismPreviewTriangle(triangle, motion);
    const OpenYAMM::Game::Mm9DatVec3 transformedPoint =
        OpenYAMM::Game::transformMm9DatMechanismPreviewPoint(sourcePoint, motion);
    const OpenYAMM::Game::Mm9DatVec3 roundTrippedPoint =
        OpenYAMM::Game::inverseTransformMm9DatMechanismPreviewPoint(transformedPoint, motion);

    CHECK(transformedPoint.x == doctest::Approx(transformedTriangle.vertices[0].x));
    CHECK(transformedPoint.y == doctest::Approx(transformedTriangle.vertices[0].y));
    CHECK(transformedPoint.z == doctest::Approx(transformedTriangle.vertices[0].z));
    CHECK(roundTrippedPoint.x == doctest::Approx(sourcePoint.x));
    CHECK(roundTrippedPoint.y == doctest::Approx(sourcePoint.y));
    CHECK(roundTrippedPoint.z == doctest::Approx(sourcePoint.z));
}

TEST_CASE("MM9 DAT world picking returns mechanism handles and can command by object id")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);
    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 1);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    CHECK(runtime.mechanismCollisionCache.stats.batchCount == 1);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = {-10.0f, 0.0f, 5.0f};
    ray.direction = {1.0f, 0.0f, 0.0f};

    OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
    options.includeWorld = false;
    options.includeObjects = false;
    options.maxDistance = 64.0f;

    const std::optional<OpenYAMM::Game::Mm9DatWorldPickHit> hit =
        OpenYAMM::Game::pickMm9DatWorldRuntime(runtime, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Mechanism);
    CHECK(hit->mechanismHandle == runtime.mechanismRuntime.mechanisms[0].handle);
    CHECK(hit->mechanismId == "mech_0");
    CHECK(hit->objectId == "door_0");
    CHECK(hit->sourceObjectIndex == 42);
    CHECK(hit->sourceModelIndex == 0);
    CHECK(hit->candidateMechanismCount > 0);
    CHECK(hit->testedMechanismCount > 0);

    const OpenYAMM::Game::Mm9DatMechanismCommandResult command =
        OpenYAMM::Game::commandMm9DatMechanismByObject(
            runtime.mechanismRuntime,
            "door_0",
            OpenYAMM::Game::Mm9DatMechanismCommand::Open);
    CHECK(command.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(runtime.mechanismRuntime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
}

TEST_CASE("MM9 DAT mechanism bounds index narrows mechanism pick candidates")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "door_a.dtx", 0.0f));
    runtime.renderMesh.triangles.push_back(visualTriangle(1, "door_b.dtx", 4096.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    for (size_t mechanismIndex = 0; mechanismIndex < 2; ++mechanismIndex)
    {
        OpenYAMM::Game::Mm9EventMechanism mechanism = {};
        mechanism.mechanismId = "mech_" + std::to_string(mechanismIndex);
        mechanism.objectId = "door_" + std::to_string(mechanismIndex);
        mechanism.sourceClass = "Door";
        mechanism.linear.hasMoveDir = true;
        mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
        mechanism.linear.hasMoveDist = true;
        mechanism.linear.moveDistLt = 10.0f;
        events.mechanisms.push_back(mechanism);

        OpenYAMM::Game::Mm9EventBinding binding = {};
        binding.objectId = mechanism.objectId;
        OpenYAMM::Game::Mm9EventBindingTarget target = {};
        target.bmodelIndex = mechanismIndex;
        target.bmodelName = "DoorModel" + std::to_string(mechanismIndex);
        binding.targets.push_back(target);
        events.bindings.push_back(binding);
    }

    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);

    REQUIRE(runtime.mechanismRuntime.stats.activeMechanismCount == 2);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 2);
    CHECK(runtime.mechanismBoundsIndex.stats.cellCount >= 2);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = {-10.0f, 0.0f, 5.0f};
    ray.direction = {1.0f, 0.0f, 0.0f};

    OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
    options.includeWorld = false;
    options.includeObjects = false;
    options.maxDistance = 64.0f;

    const std::optional<OpenYAMM::Game::Mm9DatWorldPickHit> hit =
        OpenYAMM::Game::pickMm9DatWorldRuntime(runtime, ray, options);

    REQUIRE(hit.has_value());
    CHECK(hit->kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Mechanism);
    CHECK(hit->mechanismId == "mech_0");
    CHECK(hit->candidateMechanismCount == 1);
    CHECK(hit->testedMechanismCount == 1);
}

TEST_CASE("MM9 DAT runtime use ray routes to mechanism command and syncs render batches")
{
    OpenYAMM::Game::Mm9DatWorldRuntime runtime = {};
    runtime.collisionWorld = syntheticCollisionWorld();
    runtime.renderMesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceObjectIndex = 42;
    mechanism.sourceClass = "Door";
    mechanism.sourceName = "Door0";
    mechanism.kind = "linear_door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    OpenYAMM::Game::Mm9EventTriggerOutput useTriggerOutput = {};
    useTriggerOutput.phase = "open";
    useTriggerOutput.slot = 0;
    useTriggerOutput.targetName = "DoorRelay";
    useTriggerOutput.messageName = "On";
    mechanism.triggerOutputs.push_back(useTriggerOutput);
    OpenYAMM::Game::Mm9EventMechanismSound useSound = {};
    useSound.phase = "open_start";
    useSound.sourceProperty = "OpenStartSound";
    useSound.soundName = "stone_door_open";
    useSound.authored = true;
    mechanism.sounds.push_back(useSound);
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);
    runtime.mechanismRuntime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, runtime.renderMesh);
    OpenYAMM::Game::Mm9ScriptedObject useObject = {};
    useObject.objectId = "door_0";
    useObject.sourceObjectIndex = 42;
    useObject.sourceClass = "Door";
    useObject.sourceName = "Door0";
    useObject.sourceModel = "DoorModel";
    useObject.scriptName = "Door0.scr";
    useObject.scriptParams = "param0,param1";
    useObject.x = 0.0f;
    useObject.y = 0.0f;
    useObject.z = 0.0f;
    useObject.radius = 16.0f;
    useObject.height = 64.0f;
    useObject.movement.moveToFloor = false;
    OpenYAMM::Game::Mm9ScriptedObject relayObject = {};
    relayObject.objectId = "relay_0";
    relayObject.sourceObjectIndex = 43;
    relayObject.sourceClass = "ScriptObject";
    relayObject.sourceName = "DoorRelay";
    relayObject.x = 0.0f;
    relayObject.y = 0.0f;
    relayObject.z = 0.0f;
    relayObject.radius = 16.0f;
    relayObject.height = 64.0f;
    relayObject.movement.moveToFloor = false;
    runtime.objectRegistry =
        OpenYAMM::Game::buildMm9DatObjectRegistry(
            {useObject, relayObject},
            runtime.collisionWorld,
            &runtime.mechanismRuntime);
    runtime.mechanismRenderWorld =
        OpenYAMM::Game::buildMm9DatMechanismRenderWorld(runtime.renderMesh, runtime.mechanismRuntime);
    runtime.mechanismBoundsIndex =
        OpenYAMM::Game::buildMm9DatMechanismBoundsIndex(runtime.mechanismRuntime);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 1);
    CHECK(runtime.mechanismBoundsIndex.stats.cellCount > 0);
    runtime.mechanismCollisionCache =
        OpenYAMM::Game::buildMm9DatMechanismCollisionCache(runtime.renderMesh, runtime.mechanismRuntime);
    CHECK(runtime.mechanismCollisionCache.stats.batchCount == 1);

    OpenYAMM::Game::Mm9DatPickRay ray = {};
    ray.origin = {-10.0f, 0.0f, 5.0f};
    ray.direction = {1.0f, 0.0f, 0.0f};

    OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
    options.includeWorld = false;
    options.includeObjects = false;
    options.maxDistance = 64.0f;

    const OpenYAMM::Game::Mm9DatWorldUseResult useResult =
        OpenYAMM::Game::useMm9DatWorldRuntime(
            runtime,
            ray,
            options,
            OpenYAMM::Game::Mm9DatMechanismCommand::Open);

    CHECK(useResult.picked);
    CHECK(useResult.commandAttempted);
    CHECK(useResult.activated);
    CHECK(useResult.hit.kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Mechanism);
    CHECK(useResult.mechanismCommand.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(useResult.activation.hasObject);
    CHECK(useResult.activation.hasMechanism);
    CHECK(useResult.activation.objectId == "door_0");
    CHECK(useResult.activation.objectScriptName == "Door0.scr");
    CHECK(useResult.activation.objectScriptParams == "param0,param1");
    CHECK(useResult.activation.mechanismId == "mech_0");
    CHECK(useResult.activation.mechanismKind == "linear_door");
    REQUIRE(useResult.activation.triggerOutputs.size() == 1);
    CHECK(useResult.activation.triggerOutputs[0].phase == "open");
    CHECK(useResult.activation.triggerOutputs[0].targetName == "DoorRelay");
    REQUIRE(useResult.activation.sounds.size() == 1);
    CHECK(useResult.activation.sounds[0].soundName == "stone_door_open");
    REQUIRE(useResult.triggerDispatches.size() == 1);
    CHECK(useResult.triggerDispatches[0].phase == "open");
    CHECK(useResult.triggerDispatches[0].resolvedTarget);
    CHECK(useResult.triggerDispatches[0].targetObjectId == "relay_0");
    CHECK(useResult.triggerDispatches[0].targetHandle == "relay_0");
    CHECK(useResult.triggerDispatches[0].targetSourceObjectIndex == 43);
    CHECK(useResult.triggerDispatches[0].messageName == "On");
    CHECK(runtime.mechanismRuntime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
    REQUIRE(runtime.mechanismRenderWorld.batches.size() == 1);
    CHECK(runtime.mechanismRenderWorld.batches[0].motion.progress == doctest::Approx(0.0f));

    const OpenYAMM::Game::Mm9DatWorldRuntimeUpdateStats updateStats =
        OpenYAMM::Game::updateMm9DatWorldRuntime(runtime, 0.5f);

    CHECK(updateStats.mechanisms.updatedMechanismCount == 1);
    CHECK(updateStats.mechanismRenderWorldUpdated);
    CHECK(runtime.mechanismRuntime.mechanisms[0].progress == doctest::Approx(0.5f));
    CHECK(runtime.mechanismRenderWorld.batches[0].motion.progress == doctest::Approx(0.5f));
    CHECK(updateStats.mechanisms.changedMechanismIndices.size() == 1);
    CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == 1);
    CHECK(runtime.mechanismCollisionCache.stats.transformedTriangleCount == 1);
    REQUIRE(runtime.mechanismCollisionCache.batches.size() == 1);
    REQUIRE(runtime.mechanismCollisionCache.batches[0].transformedTriangles.size() == 1);
    CHECK(runtime.mechanismCollisionCache.batches[0].motion.progress == doctest::Approx(0.5f));
    CHECK(runtime.mechanismCollisionCache.batches[0].transformedTriangles[0].vertices[0].z == doctest::Approx(12.8f));
}

TEST_CASE("MM9 DAT mechanism commands open close and toggle active mechanisms")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "mech_0";
    mechanism.objectId = "door_0";
    mechanism.sourceClass = "Door";
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    mechanism.linear.hasOpenSpeed = true;
    mechanism.linear.openSpeedLtPerSecond = 20.0f;
    mechanism.linear.hasCloseSpeed = true;
    mechanism.linear.closeSpeedLtPerSecond = 10.0f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    OpenYAMM::Game::Mm9DatMechanismRuntime runtime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, mesh);

    REQUIRE(runtime.mechanisms.size() == 1);
    const uint32_t handle = runtime.mechanisms[0].handle;

    OpenYAMM::Game::Mm9DatMechanismCommandResult command =
        OpenYAMM::Game::commandMm9DatMechanism(
            runtime,
            handle,
            OpenYAMM::Game::Mm9DatMechanismCommand::Open);
    CHECK(command.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
    CHECK(runtime.movingMechanismIndices.size() == 1);

    OpenYAMM::Game::Mm9DatMechanismUpdateStats update =
        OpenYAMM::Game::updateMm9DatMechanisms(runtime, 0.25f);
    CHECK(update.updatedMechanismCount == 1);
    CHECK(update.completedMechanismCount == 0);
    CHECK(runtime.movingMechanismIndices.size() == 1);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(0.5f));
    CHECK(runtime.mechanisms[0].motion.progress == doctest::Approx(0.5f));
    CHECK(runtime.mechanisms[0].currentBounds.valid);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 0.25f);
    CHECK(update.completedMechanismCount == 1);
    CHECK(runtime.movingMechanismIndices.empty());
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Open);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(1.0f));

    command = OpenYAMM::Game::commandMm9DatMechanism(
        runtime,
        handle,
        OpenYAMM::Game::Mm9DatMechanismCommand::Toggle);
    CHECK(command.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closing);
    CHECK(runtime.movingMechanismIndices.size() == 1);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 1.0f);
    CHECK(update.completedMechanismCount == 1);
    CHECK(runtime.movingMechanismIndices.empty());
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closed);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(0.0f));
}

TEST_CASE("MM9 DAT mechanism runtime honors authored delay wait and lock-on-close timing")
{
    OpenYAMM::Game::Mm9DatRenderMesh mesh = {};
    mesh.triangles.push_back(visualTriangle(0, "door.dtx", 0.0f));

    OpenYAMM::Game::Mm9EventsData events = {};
    OpenYAMM::Game::Mm9EventMechanism mechanism = {};
    mechanism.mechanismId = "timed_door";
    mechanism.objectId = "door_0";
    mechanism.sourceClass = "Door";
    mechanism.activation.lockOnClose = true;
    mechanism.activation.hasLockOnClose = true;
    mechanism.linear.hasMoveDir = true;
    mechanism.linear.moveDirLt = {0.0f, 1.0f, 0.0f};
    mechanism.linear.hasMoveDist = true;
    mechanism.linear.moveDistLt = 10.0f;
    mechanism.linear.hasOpenSpeed = true;
    mechanism.linear.openSpeedLtPerSecond = 10.0f;
    mechanism.linear.hasCloseSpeed = true;
    mechanism.linear.closeSpeedLtPerSecond = 10.0f;
    mechanism.timing.hasMoveDelaySecondsSource = true;
    mechanism.timing.moveDelaySecondsSource = 0.25f;
    mechanism.timing.hasOpenWaitSecondsSource = true;
    mechanism.timing.openWaitSecondsSource = 0.5f;
    events.mechanisms.push_back(mechanism);

    OpenYAMM::Game::Mm9EventBinding binding = {};
    binding.objectId = "door_0";
    OpenYAMM::Game::Mm9EventBindingTarget target = {};
    target.bmodelIndex = 0;
    target.bmodelName = "DoorModel";
    binding.targets.push_back(target);
    events.bindings.push_back(binding);

    OpenYAMM::Game::Mm9DatMechanismRuntime runtime =
        OpenYAMM::Game::buildMm9DatMechanismRuntime(events, mesh);

    REQUIRE(runtime.mechanisms.size() == 1);
    const uint32_t handle = runtime.mechanisms[0].handle;

    OpenYAMM::Game::Mm9DatMechanismCommandResult command =
        OpenYAMM::Game::commandMm9DatMechanism(
            runtime,
            handle,
            OpenYAMM::Game::Mm9DatMechanismCommand::Open);
    CHECK(command.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
    CHECK(runtime.mechanisms[0].moveDelayRemainingSeconds == doctest::Approx(0.25f));
    CHECK(runtime.movingMechanismIndices.size() == 1);

    OpenYAMM::Game::Mm9DatMechanismUpdateStats update =
        OpenYAMM::Game::updateMm9DatMechanisms(runtime, 0.25f);
    CHECK(update.updatedMechanismCount == 0);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Opening);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(0.0f));
    CHECK(runtime.movingMechanismIndices.size() == 1);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 1.0f);
    CHECK(update.completedMechanismCount == 1);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Open);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(1.0f));
    CHECK(runtime.mechanisms[0].openWaitRemainingSeconds == doctest::Approx(0.5f));
    CHECK(runtime.movingMechanismIndices.size() == 1);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 0.5f);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closing);
    CHECK(runtime.mechanisms[0].moveDelayRemainingSeconds == doctest::Approx(0.25f));
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(1.0f));
    CHECK(runtime.movingMechanismIndices.size() == 1);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 0.25f);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closing);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(1.0f));
    CHECK(runtime.movingMechanismIndices.size() == 1);

    update = OpenYAMM::Game::updateMm9DatMechanisms(runtime, 1.0f);
    CHECK(update.completedMechanismCount == 1);
    CHECK(runtime.mechanisms[0].state == OpenYAMM::Game::Mm9DatMechanismState::Closed);
    CHECK(runtime.mechanisms[0].progress == doctest::Approx(0.0f));
    CHECK(runtime.mechanisms[0].locked);
    CHECK(runtime.movingMechanismIndices.empty());
}

TEST_CASE("MM9 DAT world runtime builds native data for first acceptance maps")
{
    struct MapExpectation
    {
        std::string mapId;
        size_t datObjectCount = 0;
        bool hasVisibleWater = false;
    };

    const std::vector<MapExpectation> maps = {
        {"thjorgard", 704, true},
        {"thjorgardcity", 1771, false},
    };

    for (const MapExpectation &map : maps)
    {
        const std::string &mapId = map.mapId;
        CAPTURE(mapId);

        std::string errorMessage;
        const std::optional<OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult> loaded =
            OpenYAMM::Game::loadMm9DatLevelRuntime(levelPathForMap(mapId), errorMessage);
        REQUIRE_MESSAGE(loaded.has_value(), errorMessage.c_str());

        const OpenYAMM::Game::Mm9DatWorldRuntime &runtime = loaded->runtime;

        CHECK(runtime.mapId == mapId);
        CHECK(loaded->metadata.mapId == mapId);
        CHECK(loaded->metadata.worldBackend == "dat_world");
        CHECK(loaded->sourceDatPath.filename().generic_string().find("THJORGARD") != std::string::npos);
        CHECK(loaded->world.objects.size() == map.datObjectCount);
        CHECK(loaded->modelRoles.size() == loaded->world.worldModels.size());
        CHECK(loaded->scriptedObjects.size() == loaded->world.objects.size());
        CHECK(runtime.stats.worldModelCount == loaded->world.worldModels.size());
        CHECK(runtime.stats.renderTriangleCount > 0);
        CHECK(runtime.stats.visibleWaterTriangleCount == runtime.renderFilters.summary.visibleWaterTriangles);
        CHECK(runtime.stats.waterVolumeTriangleCount == runtime.renderFilters.summary.waterVolumeTriangles);
        CHECK(runtime.stats.renderPartitionCount > 0);
        CHECK(runtime.stats.dynamicMechanismRenderBatchCount > 0);
        CHECK(runtime.stats.dynamicMechanismTriangleCount > 0);
        CHECK(runtime.stats.preparedRenderSectionCount == runtime.preparedRenderWorld.stats.sectionCount);
        CHECK(runtime.stats.preparedRenderVertexCount == runtime.preparedRenderWorld.stats.vertexCount);
        CHECK(runtime.stats.preparedRenderIndexCount == runtime.preparedRenderWorld.stats.indexCount);
        CHECK(runtime.stats.runtimeMaterialCount == runtime.materialTable.stats.materialCount);
        CHECK(runtime.stats.runtimeMissingMaterialCount == runtime.materialTable.stats.missingMaterialCount);
        CHECK(
            runtime.stats.runtimeTextureCacheEligibleCount
            == runtime.materialTable.stats.textureCacheEligibleCount);
        CHECK(runtime.stats.runtimeMaterialCount > 0);
        CHECK(runtime.stats.runtimeTextureCacheEligibleCount > 0);
        CHECK(runtime.stats.runtimeTextureCatalogEntryCount == runtime.textureCatalog.stats.catalogEntryCount);
        CHECK(runtime.stats.runtimeTextureCatalogKeyCount == runtime.textureCatalog.stats.catalogKeyCount);
        CHECK(
            runtime.stats.runtimeResolvedTextureMaterialCount
            == runtime.textureBindings.stats.resolvedMaterialCount);
        CHECK(
            runtime.stats.runtimeMissingTextureMaterialCount
            == runtime.textureBindings.stats.missingMaterialCount);
        CHECK(runtime.stats.runtimeTextureCatalogEntryCount > 0);
        CHECK(runtime.stats.runtimeResolvedTextureMaterialCount > 0);
        CHECK(runtime.stats.renderDrawCallCount == runtime.renderSubmissionPlan.stats.drawCallCount);
        CHECK(
            runtime.stats.renderSubmittedTriangleCount
            == runtime.renderSubmissionPlan.stats.submittedTriangleCount);
        CHECK(
            runtime.stats.renderTextureMissDrawCallCount
            == runtime.renderSubmissionPlan.stats.textureMissDrawCallCount);
        CHECK(runtime.stats.renderDrawCallCount == runtime.preparedRenderWorld.stats.sectionCount);
        CHECK(runtime.stats.renderSubmittedTriangleCount == runtime.preparedRenderWorld.stats.triangleCount);
        CHECK(runtime.preparedRenderWorld.stats.staticSectionCount == runtime.renderWorld.partitions.size());
        CHECK(runtime.preparedRenderWorld.stats.dynamicSectionCount > 0);
        CHECK(runtime.preparedRenderWorld.stats.staticTriangleCount > 0);
        CHECK(runtime.preparedRenderWorld.stats.dynamicTriangleCount > 0);
        if (map.hasVisibleWater)
        {
            CHECK(runtime.stats.visibleWaterTriangleCount > 0);
            CHECK(runtime.renderWorld.stats.visibleWaterTriangleCount > 0);
        }
        else
        {
            CHECK(runtime.stats.visibleWaterTriangleCount == 0);
            CHECK(runtime.renderWorld.stats.visibleWaterTriangleCount == 0);
        }
        CHECK(runtime.stats.waterVolumeTriangleCount > 0);
        CHECK(runtime.renderWorld.stats.waterVolumeSkippedTriangleCount > 0);
        CHECK(runtime.stats.collisionTriangleCount > 0);
        CHECK(runtime.stats.collisionCellCount > 0);
        CHECK(runtime.stats.objectCount == loaded->scriptedObjects.size());
        CHECK(runtime.stats.renderableObjectCount == runtime.objectRegistry.stats.renderableObjectCount);
        CHECK(runtime.stats.collidableObjectCount == runtime.objectRegistry.stats.collidableObjectCount);
        CHECK(runtime.stats.collidableObjectCellCount == runtime.objectRegistry.stats.collidableCellCount);
        CHECK(runtime.stats.collidableObjectCellRefs == runtime.objectRegistry.stats.collidableCellObjectRefs);
        CHECK(runtime.stats.maxCollidableObjectCellRefs == runtime.objectRegistry.stats.maxCollidableCellObjectRefs);
        CHECK(runtime.stats.actorObjectCellCount == runtime.objectRegistry.stats.actorCellCount);
        CHECK(runtime.stats.actorObjectCellRefs == runtime.objectRegistry.stats.actorCellObjectRefs);
        CHECK(runtime.stats.maxActorObjectCellRefs == runtime.objectRegistry.stats.maxActorCellObjectRefs);
        CHECK(runtime.stats.objectRenderInstanceCount == runtime.objectPresentationWorld.stats.instanceCount);
        CHECK(runtime.stats.actorRenderInstanceCount == runtime.objectPresentationWorld.stats.actorInstanceCount);
        CHECK(runtime.stats.propRenderInstanceCount == runtime.objectPresentationWorld.stats.propInstanceCount);
        CHECK(
            runtime.stats.objectRenderModelAssetInstanceCount
            == runtime.objectPresentationWorld.stats.modelAssetInstanceCount);
        CHECK(
            runtime.stats.objectRenderSourceModelWithoutAssetCount
            == runtime.objectPresentationWorld.stats.sourceModelWithoutModelAssetCount);
        CHECK(runtime.stats.interactableObjectCount == runtime.objectRegistry.stats.interactableObjectCount);
        CHECK(runtime.stats.actorObjectCount == runtime.objectRegistry.stats.actorObjectCount);
        CHECK(runtime.stats.propObjectCount == runtime.objectRegistry.stats.propObjectCount);
        CHECK(runtime.stats.triggerObjectCount == runtime.objectRegistry.stats.triggerObjectCount);
        CHECK(runtime.stats.mechanismObjectCount == runtime.objectRegistry.stats.mechanismObjectCount);
        CHECK(runtime.stats.tickingObjectCount == runtime.objectRegistry.stats.tickingObjectCount);
        CHECK(runtime.objectRegistry.stats.renderableObjectCount > 0);
        CHECK(runtime.objectPresentationWorld.stats.instanceCount > 0);
        CHECK(runtime.objectPresentationWorld.stats.sourceModelInstanceCount > 0);
        const OpenYAMM::Game::Mm9DatObjectModelRenderPlan objectModelRenderPlan =
            OpenYAMM::Game::buildMm9DatObjectModelRenderPlan(
                runtime.objectPresentationWorld,
                loaded->scriptedObjects);
        CHECK(
            objectModelRenderPlan.stats.presentationInstanceCount
            == runtime.objectPresentationWorld.stats.instanceCount);
        CHECK(
            objectModelRenderPlan.stats.candidateInstanceCount
            == runtime.objectPresentationWorld.stats.sourceModelInstanceCount);
        CHECK(
            objectModelRenderPlan.stats.sourceModelCandidateCount
            == runtime.objectPresentationWorld.stats.sourceModelInstanceCount);
        CHECK(objectModelRenderPlan.stats.missingScriptedObjectCount == 0);
        CHECK(
            objectModelRenderPlan.stats.scriptedObjectMatchCount
            == objectModelRenderPlan.stats.candidateInstanceCount);
        CHECK(
            objectModelRenderPlan.stats.renderInstanceCount
            == objectModelRenderPlan.stats.candidateInstanceCount);
        CHECK(objectModelRenderPlan.stats.renderInstanceCount > 0);
        CHECK(objectModelRenderPlan.instances.size() == objectModelRenderPlan.stats.renderInstanceCount);
        OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
        std::string resolverError;
        REQUIRE_MESSAGE(
            resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", resolverError),
            resolverError.c_str());
        size_t resolvedModelInstanceCount = 0;
        size_t unresolvedModelInstanceCount = 0;
        size_t initializedVisualCount = 0;
        size_t totalDrawItemCount = 0;
        std::string unresolvedModelExamples;
        std::unordered_map<std::string, OpenYAMM::Game::AnimatedModelAsset> assetCache;
        for (const OpenYAMM::Game::Mm9DatObjectModelRenderInstance &instance :
            objectModelRenderPlan.instances)
        {
            CHECK(instance.object.x == doctest::Approx(instance.runtimePosition.x));
            CHECK(instance.object.y == doctest::Approx(instance.runtimePosition.z));
            CHECK(instance.object.z == doctest::Approx(instance.runtimePosition.y));
            CHECK_FALSE(instance.object.sourceModel.empty());

            std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
            const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
                OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(
                    instance.object,
                    resolver,
                    diagnostics);
            if (resolved.has_value())
            {
                ++resolvedModelInstanceCount;
                const std::string assetKey = resolved->resolution.modelAssetPath.generic_string();
                if (assetCache.find(assetKey) == assetCache.end())
                {
                    assetCache.emplace(assetKey, loadMm9ResolvedModel(resolved->resolution));
                }

                const OpenYAMM::Game::AnimatedModelAsset &asset = assetCache.at(assetKey);
                OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
                OpenYAMM::Game::initializeMm9AnimatedActorVisual(
                    resolved->source,
                    resolved->resolution,
                    asset,
                    visual);
                CHECK(visual.visible);
                CHECK(visual.worldBounds.valid);
                CHECK_FALSE(visual.renderPrepCache.drawItems.empty());
                totalDrawItemCount += visual.renderPrepCache.drawItems.size();
                ++initializedVisualCount;
            }
            else
            {
                if (unresolvedModelInstanceCount < 8)
                {
                    unresolvedModelExamples += instance.object.sourceModel
                        + " skin=" + instance.object.sourceSkin
                        + " class=" + instance.object.sourceClass
                        + " name=" + instance.object.sourceName
                        + "\n";
                }
                ++unresolvedModelInstanceCount;
            }
        }
        CHECK_MESSAGE(unresolvedModelInstanceCount == 0, unresolvedModelExamples);
        CHECK(resolvedModelInstanceCount == objectModelRenderPlan.stats.renderInstanceCount);
        CHECK(initializedVisualCount == objectModelRenderPlan.stats.renderInstanceCount);
        CHECK(totalDrawItemCount >= initializedVisualCount);
        CHECK(runtime.objectRegistry.stats.collidableObjectCount > 0);
        CHECK(runtime.objectRegistry.stats.collidableCellCount > 0);
        CHECK(
            runtime.objectRegistry.stats.collidableCellObjectRefs
            >= runtime.objectRegistry.stats.collidableObjectCount);
        CHECK(runtime.objectRegistry.stats.maxCollidableCellObjectRefs > 0);
        CHECK(runtime.objectRegistry.stats.actorCellCount > 0);
        CHECK(runtime.objectRegistry.stats.actorCellObjectRefs >= runtime.objectRegistry.stats.actorObjectCount);
        CHECK(runtime.objectRegistry.stats.maxActorCellObjectRefs > 0);
        CHECK(runtime.objectRegistry.stats.interactableObjectCount > 0);
        CHECK(runtime.objectRegistry.stats.moveToFloorObjectCount > 0);
        CHECK(runtime.objectRegistry.stats.policySkippedMoveToFloorCount > 0);
        CHECK(runtime.stats.snappedToFloorCount > 0);
        CHECK(runtime.lightLayer.worldInfo.rawPropertyString == loaded->world.worldInfo.propertyString);
        CHECK(runtime.stats.lightCount == runtime.lightLayer.lights.size());
        CHECK(runtime.stats.lightCount > 0);
        CHECK(runtime.stats.staticRenderLightCount == runtime.staticRenderLights.size());
        CHECK(runtime.stats.skyDefinitionCount == runtime.skyLayer.definitions.size());
        CHECK(runtime.stats.skyObjectCount == runtime.skyLayer.objects.size());
        CHECK(runtime.stats.skyModelCount == runtime.skyLayer.skyModelIndices.size());
        CHECK(runtime.stats.skyModelCount > 0);
        CHECK(runtime.renderWorld.stats.helperSkippedTriangleCount > 0);
        CHECK(runtime.collisionWorld.stats().maxCellTriangleRefs < runtime.stats.collisionTriangleCount);
        CHECK(loaded->events.objects.size() == loaded->world.objects.size());
        CHECK(loaded->events.mechanisms.size() > 0);
        CHECK(loaded->events.bindings.size() > 0);
        CHECK(runtime.stats.mechanismCount == loaded->events.mechanisms.size());
        CHECK(runtime.stats.activeMechanismCount > 0);
        CHECK(runtime.mechanismRuntime.mechanismIndexByObjectId.size() > 0);
        CHECK(runtime.mechanismRuntime.mechanismIndexByObjectId.size() <= runtime.stats.mechanismCount);
        CHECK(runtime.mechanismRuntime.stats.changedBoundsCount > 0);
        CHECK(runtime.mechanismBoundsIndex.stats.indexedMechanismCount == runtime.stats.activeMechanismCount);
        CHECK(runtime.stats.mechanismBoundsCellCount == runtime.mechanismBoundsIndex.stats.cellCount);
        CHECK(runtime.stats.mechanismBoundsCellRefs == runtime.mechanismBoundsIndex.stats.mechanismCellRefs);
        CHECK(runtime.stats.mechanismBoundsCellCount > 0);
        CHECK(runtime.stats.mechanismCollisionBatchCount == runtime.mechanismCollisionCache.stats.batchCount);
        CHECK(
            runtime.mechanismCollisionCache.stats.indexedBatchCount
            == runtime.mechanismCollisionCache.stats.batchCount);
        CHECK(
            runtime.stats.mechanismCollisionTriangleCount
            == runtime.mechanismCollisionCache.stats.transformedTriangleCount);
        CHECK(runtime.stats.mechanismCollisionBatchCount == runtime.stats.activeMechanismCount);
        CHECK(runtime.stats.mechanismCollisionTriangleCount > 0);

        for (const OpenYAMM::Game::Mm9DatMechanismRenderBatch &batch : runtime.mechanismRenderWorld.batches)
        {
            for (const OpenYAMM::Game::Mm9DatRenderPartition &partition : runtime.renderWorld.partitions)
            {
                CHECK(partition.sourceModelIndex != batch.sourceModelIndex);
            }
        }
    }
}

TEST_CASE("MM9 DAT acceptance maps activate native DAT mechanisms through use rays")
{
    const std::vector<std::string> mapIds = {
        "thjorgard",
        "thjorgardcity",
    };

    for (const std::string &mapId : mapIds)
    {
        CAPTURE(mapId);

        std::string errorMessage;
        std::optional<OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult> loaded =
            OpenYAMM::Game::loadMm9DatLevelRuntime(levelPathForMap(mapId), errorMessage);
        REQUIRE_MESSAGE(loaded.has_value(), errorMessage.c_str());

        OpenYAMM::Game::Mm9DatWorldRuntime &runtime = loaded->runtime;
        const OpenYAMM::Game::Mm9DatMechanismInstance *pMechanism = nullptr;
        for (const OpenYAMM::Game::Mm9DatMechanismInstance &mechanism :
            runtime.mechanismRuntime.mechanisms)
        {
            if (mechanism.active && !mechanism.inert && mechanism.currentBounds.valid)
            {
                pMechanism = &mechanism;
                break;
            }
        }

        REQUIRE(pMechanism != nullptr);
        const OpenYAMM::Game::Mm9DatRenderBounds bounds = pMechanism->currentBounds;
        const float xExtent = bounds.max.x - bounds.min.x;
        const float zExtent = bounds.max.z - bounds.min.z;

        OpenYAMM::Game::Mm9DatPickRay ray = {};
        ray.origin = bounds.center;
        if (xExtent >= zExtent)
        {
            ray.origin.x = bounds.min.x - 64.0f;
            ray.direction = {1.0f, 0.0f, 0.0f};
        }
        else
        {
            ray.origin.z = bounds.min.z - 64.0f;
            ray.direction = {0.0f, 0.0f, 1.0f};
        }

        OpenYAMM::Game::Mm9DatWorldPickOptions options = {};
        options.includeWorld = false;
        options.includeObjects = false;
        options.includeMechanisms = true;
        options.maxDistance = std::max(xExtent, zExtent) + 256.0f;

        const OpenYAMM::Game::Mm9DatWorldUseResult useResult =
            OpenYAMM::Game::useMm9DatWorldRuntime(
                runtime,
                ray,
                options,
                OpenYAMM::Game::Mm9DatMechanismCommand::Toggle,
                true);

        CHECK(useResult.picked);
        CHECK(useResult.commandAttempted);
        CHECK(useResult.activated);
        CHECK(useResult.hit.kind == OpenYAMM::Game::Mm9DatWorldPickHitKind::Mechanism);
        CHECK(useResult.hit.candidateMechanismCount > 0);
        CHECK(useResult.hit.testedMechanismCount > 0);
        CHECK(useResult.mechanismCommand.status == OpenYAMM::Game::Mm9DatMechanismCommandStatus::Applied);
        CHECK(useResult.activation.hasMechanism);
        CHECK_FALSE(useResult.activation.mechanismId.empty());
        CHECK_FALSE(useResult.activation.objectId.empty());
        CHECK(runtime.mechanismRuntime.movingMechanismIndices.size() > 0);
        CHECK(runtime.stats.mechanismBoundsCellCount == runtime.mechanismBoundsIndex.stats.cellCount);
        CHECK(
            runtime.stats.mechanismCollisionTriangleCount
            == runtime.mechanismCollisionCache.stats.transformedTriangleCount);
    }
}

TEST_CASE("MM9 DAT runtime extracts StartPoint and ExitTrigger route data from DAT")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult> thjorgard =
        OpenYAMM::Game::loadMm9DatLevelRuntimeForMap(sourceRoot(), "thjorgard", errorMessage);
    REQUIRE_MESSAGE(thjorgard.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult> thjorgardCity =
        OpenYAMM::Game::loadMm9DatLevelRuntimeForMap(sourceRoot(), "thjorgardcity", errorMessage);
    REQUIRE_MESSAGE(thjorgardCity.has_value(), errorMessage.c_str());

    const auto findStartPoint =
        [](const OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult &level, const std::string &name)
        -> const OpenYAMM::Game::Mm9DatRuntimeStartPoint *
        {
            const auto iterator = std::find_if(
                level.startPoints.begin(),
                level.startPoints.end(),
                [&name](const OpenYAMM::Game::Mm9DatRuntimeStartPoint &startPoint)
                {
                    return startPoint.name == name;
                });
            return iterator != level.startPoints.end() ? &*iterator : nullptr;
        };

    const auto findExitTrigger =
        [](const OpenYAMM::Game::Mm9DatLevelRuntimeLoadResult &level, const std::string &name)
        -> const OpenYAMM::Game::Mm9DatRuntimeExitTrigger *
        {
            const auto iterator = std::find_if(
                level.exitTriggers.begin(),
                level.exitTriggers.end(),
                [&name](const OpenYAMM::Game::Mm9DatRuntimeExitTrigger &exitTrigger)
                {
                    return exitTrigger.name == name;
                });
            return iterator != level.exitTriggers.end() ? &*iterator : nullptr;
        };

    const OpenYAMM::Game::Mm9DatRuntimeExitTrigger *pTerrainExit =
        findExitTrigger(*thjorgard, "ExitTrigger4");
    REQUIRE(pTerrainExit != nullptr);
    CHECK(pTerrainExit->destinationWorld == "ThjorgardCity");
    CHECK(pTerrainExit->destinationMapId == "thjorgardcity");
    CHECK(pTerrainExit->startPointName == "StartPointTerrain");
    CHECK(pTerrainExit->travelDays == doctest::Approx(0.0f));
    CHECK(pTerrainExit->askPlayer);
    CHECK(pTerrainExit->startOn);
    CHECK(pTerrainExit->positionLt.x == doctest::Approx(-1952.0f));
    CHECK(pTerrainExit->positionLt.y == doctest::Approx(762.0f));
    CHECK(pTerrainExit->positionLt.z == doctest::Approx(3836.0f));

    const OpenYAMM::Game::Mm9DatRuntimeStartPoint *pCityTerrainStart =
        findStartPoint(*thjorgardCity, "StartPointTerrain");
    REQUIRE(pCityTerrainStart != nullptr);
    CHECK(pCityTerrainStart->movePlayerToFloor);
    CHECK(pCityTerrainStart->positionLt.x == doctest::Approx(-3136.0f));
    CHECK(pCityTerrainStart->positionLt.y == doctest::Approx(88.000015f));
    CHECK(pCityTerrainStart->positionLt.z == doctest::Approx(1280.0f));
    CHECK(pCityTerrainStart->yawRadians == doctest::Approx(0.8726646f));

    const OpenYAMM::Game::Mm9DatRuntimeExitTrigger *pCityDockExit =
        findExitTrigger(*thjorgardCity, "Thjorgarddocks");
    REQUIRE(pCityDockExit != nullptr);
    CHECK(pCityDockExit->destinationWorld == "Thjorgard");
    CHECK(pCityDockExit->destinationMapId == "thjorgard");
    CHECK(pCityDockExit->startPointName == "ThjorgardCityDockExit");

    const OpenYAMM::Game::Mm9DatRuntimeStartPoint *pThjorgardDockStart =
        findStartPoint(*thjorgard, "ThjorgardCityDockExit");
    REQUIRE(pThjorgardDockStart != nullptr);
    CHECK(pThjorgardDockStart->movePlayerToFloor);
    CHECK(pThjorgardDockStart->yawRadians == doctest::Approx(4.7123890f));
}

TEST_CASE("MM9 DAT dev entry loads first acceptance maps and derives start poses from DAT")
{
    struct DevEntryExpectation
    {
        std::string mapId;
        std::string preferredStartName;
    };

    const std::vector<DevEntryExpectation> maps = {
        {"thjorgard", "ThjorgardCityTerrainExit"},
        {"thjorgardcity", "StartPointTerrain"},
    };

    for (const DevEntryExpectation &map : maps)
    {
        CAPTURE(map.mapId);

        OpenYAMM::Game::Mm9DatRuntimeDevEntryRequest request = {};
        request.sourceRoot = sourceRoot();
        request.mapId = map.mapId;
        request.preferredStartName = map.preferredStartName;

        std::string errorMessage;
        const std::optional<OpenYAMM::Game::Mm9DatRuntimeDevEntryResult> entry =
            OpenYAMM::Game::loadMm9DatRuntimeForDevEntry(request, errorMessage);

        REQUIRE_MESSAGE(entry.has_value(), errorMessage.c_str());
        CHECK(entry->level.metadata.mapId == map.mapId);
        CHECK(entry->level.metadata.worldBackend == "dat_world");
        CHECK(entry->startPose.mapId == map.mapId);
        CHECK(entry->startPose.source == OpenYAMM::Game::Mm9DatDevStartPoseSource::PreferredStartPoint);
        CHECK(entry->startPose.sourceName == map.preferredStartName);
        CHECK(entry->startPose.hasSourceObject);
        CHECK(entry->startPose.snappedToFloor);
        CHECK(std::isfinite(entry->startPose.yawRadians));
        CHECK(entry->startPose.floorCandidateTriangleCount > 0);
        CHECK(entry->startPose.floorTestedTriangleCount > 0);
        CHECK(entry->level.runtime.stats.renderTriangleCount > 0);
        CHECK(entry->level.runtime.stats.collisionTriangleCount > 0);
        CHECK(entry->level.runtime.stats.activeMechanismCount > 0);
    }
}

TEST_CASE("MM9 DAT dev entry native movement ticks stay grounded on first acceptance maps")
{
    struct DevEntryExpectation
    {
        std::string mapId;
        std::string preferredStartName;
    };

    const std::vector<DevEntryExpectation> maps = {
        {"thjorgard", "ThjorgardCityTerrainExit"},
        {"thjorgardcity", "StartPointTerrain"},
    };

    for (const DevEntryExpectation &map : maps)
    {
        CAPTURE(map.mapId);

        OpenYAMM::Game::Mm9DatRuntimeDevEntryRequest request = {};
        request.sourceRoot = sourceRoot();
        request.mapId = map.mapId;
        request.preferredStartName = map.preferredStartName;

        std::string errorMessage;
        std::optional<OpenYAMM::Game::Mm9DatRuntimeDevEntryResult> entry =
            OpenYAMM::Game::loadMm9DatRuntimeForDevEntry(request, errorMessage);

        REQUIRE_MESSAGE(entry.has_value(), errorMessage.c_str());

        OpenYAMM::Game::Mm9DatPartyRuntimeState partyState =
            OpenYAMM::Game::initializeMm9DatPartyRuntimeState(entry->startPose);
        REQUIRE(partyState.onGround);
        CHECK(isFiniteVec3(partyState.position));

        OpenYAMM::Game::Mm9DatPartyRuntimeMovementOptions movementOptions = {};
        movementOptions.halfHeight = request.partyHalfHeight;
        movementOptions.floorSnapDistance = 128.0f;

        OpenYAMM::Game::Mm9DatPartyRuntimeMoveInput input = {};
        input.deltaSeconds = 0.1f;

        const OpenYAMM::Game::Mm9DatPartyRuntimeMoveResult moveResult =
            OpenYAMM::Game::moveMm9DatPartyRuntime(
                entry->level.runtime,
                partyState,
                input,
                movementOptions);

        CHECK(moveResult.movement.onGround);
        CHECK(partyState.onGround);
        const bool hasFloorSupport =
            moveResult.movement.floorHit.has_value() || moveResult.movement.mechanismFloorHit.has_value();
        const bool queriedFloorCandidates =
            moveResult.movement.floorCandidateTriangleCount > 0
            || moveResult.movement.mechanismCandidateTriangleCount > 0;
        const bool testedFloorCandidates =
            moveResult.movement.floorTestedTriangleCount > 0
            || moveResult.movement.mechanismTestedTriangleCount > 0;
        CHECK(hasFloorSupport);
        CHECK(queriedFloorCandidates);
        CHECK(testedFloorCandidates);
        CHECK_FALSE(moveResult.movement.blockedByWall);
        CHECK_FALSE(moveResult.movement.blockedByObject);
        CHECK(moveResult.newVerticalVelocityLtPerSecond == doctest::Approx(0.0f));
        CHECK(partyState.verticalVelocityLtPerSecond == doctest::Approx(0.0f));
        CHECK(isFiniteVec3(moveResult.movement.finalPosition));
        CHECK(isFiniteVec3(partyState.position));
    }
}
