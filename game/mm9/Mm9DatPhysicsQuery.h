#pragma once

#include "game/mm9/Mm9DatWorld.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
constexpr uint32_t Mm9DatPhysicsQueryChannelVisible = 0x00000001u;
constexpr uint32_t Mm9DatPhysicsQueryChannelPhysics = 0x00000002u;
constexpr uint32_t Mm9DatPhysicsQueryChannelVisibility = 0x00000004u;
constexpr uint32_t Mm9DatPhysicsQueryChannelTrigger = 0x00000008u;
constexpr uint32_t Mm9DatPhysicsQueryChannelWater = 0x00000010u;
constexpr uint32_t Mm9DatPhysicsQueryChannelSky = 0x00000020u;
constexpr uint32_t Mm9DatPhysicsQueryChannelMovable = 0x00000040u;
constexpr uint32_t Mm9DatPhysicsQueryChannelHelper = 0x00000080u;
constexpr uint32_t Mm9DatPhysicsQueryChannelAll = 0x000000ffu;

struct Mm9DatPhysicsSourceRef
{
    size_t queryTriangleIndex = 0;
    size_t renderTriangleIndex = 0;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    size_t sourceTextureIndex = 0;
    std::string sourceTexture;
    uint32_t surfaceFlags = 0;
    uint16_t textureFlags = 0;
    uint32_t channelFlags = 0;
};

struct Mm9DatPhysicsQueryTriangle
{
    Mm9DatPhysicsSourceRef source;
    Mm9DatVec3 vertex0;
    Mm9DatVec3 vertex1;
    Mm9DatVec3 vertex2;
    Mm9DatVec3 normal;
    float planeDistance = 0.0f;
};

struct Mm9DatPhysicsQueryStats
{
    size_t totalTriangles = 0;
    size_t visibleTriangles = 0;
    size_t physicsTriangles = 0;
    size_t visibilityTriangles = 0;
    size_t triggerTriangles = 0;
    size_t waterTriangles = 0;
    size_t skyTriangles = 0;
    size_t movableTriangles = 0;
    size_t helperTriangles = 0;
    size_t unclassifiedTriangles = 0;
    size_t sourceModelCount = 0;
    bool hasPhysicsGeometry = false;
    bool hasVisibilityGeometry = false;
    std::vector<std::string> warnings;
};

struct Mm9DatPhysicsQueryView
{
    std::vector<Mm9DatPhysicsQueryTriangle> triangles;
    Mm9DatPhysicsQueryStats stats;
};

struct Mm9DatPhysicsRaycastOptions
{
    uint32_t channelMask = Mm9DatPhysicsQueryChannelPhysics;
    float maxDistance = 0.0f;
    bool hasMaxDistance = false;
    bool includeBackfaces = true;
};

struct Mm9DatPhysicsRayHit
{
    Mm9DatVec3 point;
    Mm9DatVec3 normal;
    float planeDistance = 0.0f;
    float distance = 0.0f;
    float barycentricU = 0.0f;
    float barycentricV = 0.0f;
    Mm9DatPhysicsSourceRef source;
    uint32_t channelFlags = 0;
};

Mm9DatPhysicsQueryView buildMm9DatPhysicsQueryView(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderFilterResult &filters);

std::optional<Mm9DatPhysicsRayHit> raycastMm9DatPhysicsQueryView(
    const Mm9DatPhysicsQueryView &view,
    const Mm9DatPickRay &ray,
    const Mm9DatPhysicsRaycastOptions &options = {});

std::optional<Mm9DatPhysicsRayHit> segmentcastMm9DatPhysicsQueryView(
    const Mm9DatPhysicsQueryView &view,
    const Mm9DatVec3 &start,
    const Mm9DatVec3 &end,
    const Mm9DatPhysicsRaycastOptions &options = {});

Mm9DatVec3 projectMm9DatPhysicsVelocityAlongPlane(
    const Mm9DatVec3 &velocity,
    const Mm9DatVec3 &normal);
}
