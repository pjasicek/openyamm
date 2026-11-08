#pragma once

#include "game/indoor/IndoorMapData.h"

#include <bx/math.h>

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct EventRuntimeState;
struct IndoorPortalGraph;
struct MapDeltaData;

struct IndoorVisibilityPlane
{
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

using IndoorVisibilityFrustum = std::vector<IndoorVisibilityPlane>;

struct IndoorVisibilityNode
{
    int16_t sectorId = -1;
    int16_t parentNodeIndex = -1;
    int16_t entryPortalFaceId = -1;
    uint16_t depth = 0;
    IndoorVisibilityFrustum frustumPlanes;
};

struct IndoorPortalVisibilityTrace
{
    int16_t sourceSectorId = -1;
    int16_t targetSectorId = -1;
    uint16_t faceId = 0;
    uint16_t portalLinkId = 0;
    uint16_t depth = 0;
    bool accepted = false;
    std::string reason;
};

struct IndoorAcceptedPortalVisibility
{
    int16_t targetSectorId = -1;
    uint16_t faceId = 0;
};

inline bool indoorGeometrySectorsVisible(std::span<const uint8_t> visibleSectors,
    int16_t sectorId, int16_t backSectorId)
{
    const bool frontKnown = sectorId >= 0 && size_t(sectorId) < visibleSectors.size();
    const bool backKnown = backSectorId >= 0 && size_t(backSectorId) < visibleSectors.size();
    return (!frontKnown && !backKnown) || (frontKnown && visibleSectors[sectorId] != 0)
        || (backKnown && visibleSectors[backSectorId] != 0);
}

struct IndoorPortalVisibilityInput
{
    const IndoorMapData *pMapData = nullptr;
    const IndoorPortalGraph *pPortalGraph = nullptr;
    const std::vector<IndoorVertex> *pVertices = nullptr;
    const MapDeltaData *pMapDeltaData = nullptr;
    const std::optional<EventRuntimeState> *pEventRuntimeState = nullptr;
    bx::Vec3 cameraPosition = {0.0f, 0.0f, 0.0f};
    bx::Vec3 cameraForward = {1.0f, 0.0f, 0.0f};
    bx::Vec3 cameraUp = {0.0f, 0.0f, 1.0f};
    float verticalFovDegrees = 60.0f;
    float aspectRatio = 1.0f;
    // Render queries also reject apertures collapsed to a single screen row, as in MM8.
    // Zero leaves gameplay geometry queries independent of framebuffer resolution.
    int viewportHeight = 0;
    int16_t startSectorId = -1;
    uint16_t maxNodes = 256;
    uint16_t maxDepth = 32;
    // The view distance of a map with the outdoor view (devdocs/INDOOR_OPEN_SKY.md "Outdoor view"): a portal whose
    // nearest visible point is deeper (view depth, as the far plane) is not entered. 0: no limit (every other map).
    float maxDistance = 0.0f;
    // A portal that the view would drop (facing away or clipped off) still passes on the view it is reached through
    // (the whole view at the start sector) when the camera is within this distance of its plane and its bounds
    // (IndoorMapData::portalNearReach, the scene's `portal_visibility`). 0: MM8's rule only (9 units of the plane, 16
    // of the bounds, the start sector's portals), every MM6-MM8 map.
    float nearPortalReach = 0.0f;
    bool collectPortalTraces = true;
};

struct IndoorPortalVisibilityResult
{
    std::vector<uint8_t> visibleSectorMask;
    std::vector<IndoorVisibilityNode> nodes;
    std::vector<std::vector<uint16_t>> nodeIndicesBySector;
    std::vector<std::vector<IndoorVisibilityFrustum>> frustumsBySector;
    std::vector<IndoorAcceptedPortalVisibility> acceptedPortals;
    std::vector<IndoorPortalVisibilityTrace> portalTraces;
    uint32_t portalCandidateCount = 0;
    uint32_t acceptedPortalCount = 0;
    uint32_t rejectedPortalCount = 0;
    uint32_t invalidPortalCount = 0;
    uint32_t ancestorRejectedPortalCount = 0;
    uint32_t directionRejectedPortalCount = 0;
    uint32_t clippedPortalRejectedCount = 0;
    uint32_t orphanVisibleSectorCount = 0;
    bool maxNodeLimitHit = false;
};

IndoorPortalVisibilityResult buildIndoorPortalVisibility(const IndoorPortalVisibilityInput &input);
}
