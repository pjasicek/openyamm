#pragma once

#include <bx/math.h>

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The indoor portal and visibility debug view (console `portals`, tools/RUN_GAME.md "Indoor portal view"). Off by
// default; while off the renderer tests one flag per frame and does nothing else for it. It works on every BLV.
enum class IndoorPortalDebugFaces : uint8_t
{
    Off,
    // Every portal face of the map, translucent cyan; the ones traversed this frame brighter.
    All,
    // Only the portal faces the visibility traversal passed through this frame.
    Traversed
};

struct IndoorPortalDebugSettings
{
    IndoorPortalDebugFaces faces = IndoorPortalDebugFaces::Off;
    // The drawn sectors' faces outlined in a colour per sector, with the sector ids at the traversed portals.
    bool sectors = false;
    // The on-screen readout of counts and timings.
    bool readout = false;
    // Each pass in its own bgfx view (decorations, actors, open sky, translucent), with the bgfx profiler on, so the
    // readout shows each pass's GPU time. Transparencies then draw before ambient occlusion.
    bool gpuPasses = false;
    // Rebuild the portal visibility every frame, as walking does (a still camera reuses it).
    bool rebuildEveryFrame = false;
    // A `[PortalView]` line with the counts once per second.
    bool log = false;
    // The plan cell size of the tile estimate: a sector's batches split into cells this wide, each culled against
    // the sector's portal frustums.
    float tileSize = 1024.0f;

    bool active() const
    {
        return faces != IndoorPortalDebugFaces::Off || sectors || readout || gpuPasses || rebuildEveryFrame || log;
    }
};

// The passes that `portals gpu` moves into their own views, in drawing order after the world view.
enum class IndoorDebugPass : uint8_t
{
    Decorations,
    Actors,
    OpenSky,
    Translucent,
    Count
};

const char *indoorDebugPassName(IndoorDebugPass pass);

struct IndoorPortalDebugSector
{
    int16_t sectorId = -1;
    // Faces the sector has in the drawn batches (whether drawn this frame or not).
    uint32_t totalFaces = 0;
    // Submitted this frame: batches, faces and triangles.
    uint32_t batches = 0;
    uint32_t faces = 0;
    uint32_t triangles = 0;
    // Of those faces: in the camera frustum, and in the sector's portal frustums (what a perfect cull would keep).
    uint32_t facesInView = 0;
    uint32_t facesInPortals = 0;
    uint32_t trianglesInPortals = 0;
    // The tile estimate: (batch, cell) pairs in the portal frustums and their triangles.
    uint32_t tileDraws = 0;
    uint32_t tileTriangles = 0;
    // Portal candidates the traversal tested from this sector: its portal links once per traversal node in it.
    uint32_t portalsTested = 0;
    uint32_t nodes = 0;
    uint32_t portalLinks = 0;
};

struct IndoorPortalDebugLabel
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    int16_t sectorId = -1;
};

struct IndoorPortalDebugStats
{
    bool valid = false;
    int16_t eyeSectorId = -1;
    std::array<float, 3> eye = {};
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    // Visibility: sectors drawn, traversal nodes, portal candidates tested and passed, and the rejections.
    uint32_t sectorsDrawn = 0;
    uint32_t visibilityNodes = 0;
    uint32_t portalsTested = 0;
    uint32_t portalsTraversed = 0;
    uint32_t portalsRejectedFacing = 0;
    uint32_t portalsRejectedClipped = 0;
    uint32_t portalsRejectedOther = 0;
    bool visibilityRebuilt = false;
    // The last visibility build (this frame's, or the cached one's).
    uint64_t visibilityBuildNanoseconds = 0;
    // World faces submitted (opaque batches: one sector's faces of one texture) and their share in the camera and
    // portal frustums.
    uint32_t batchesSubmitted = 0;
    uint32_t facesSubmitted = 0;
    uint32_t trianglesSubmitted = 0;
    uint32_t facesInView = 0;
    uint32_t facesInPortals = 0;
    uint32_t trianglesInPortals = 0;
    uint32_t tileDraws = 0;
    uint32_t tileTriangles = 0;
    // Distinct textures (with lightmap pages) among the submitted batches.
    uint32_t batchTextures = 0;
    // The world face draw calls: the submitted batches merged by draw group (IndoorFaceDrawGroups.h).
    uint32_t faceDraws = 0;
    // CPU nanoseconds this frame.
    uint64_t cpuVisibilityNanoseconds = 0;
    uint64_t cpuLightingNanoseconds = 0;
    uint64_t cpuFacesNanoseconds = 0;
    uint64_t cpuDecorationsNanoseconds = 0;
    uint64_t cpuActorsNanoseconds = 0;
    uint64_t cpuOpenSkyNanoseconds = 0;
    uint64_t cpuTranslucentNanoseconds = 0;
    uint64_t cpuTotalNanoseconds = 0;
    // The drawn sectors, most submitted faces first.
    std::vector<IndoorPortalDebugSector> sectors;
    // The sector ids at the centres of the traversed portals.
    std::vector<IndoorPortalDebugLabel> labels;
};

// A distinct, stable colour per sector (ABGR, opaque).
uint32_t indoorPortalDebugSectorColor(int16_t sectorId);

// The counts as `key=value` pairs and the drawn sectors as `sectors=id:faces/facesInPortals/triangles/batches/
// tileDraws/tileTriangles/portalsTested/totalFaces/nodes/portalLinks,...` (one line, for the log and the console).
std::string describeIndoorPortalDebugStats(const IndoorPortalDebugStats &stats);
}
