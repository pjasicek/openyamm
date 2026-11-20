#pragma once

#include "game/indoor/IndoorMovers.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{

// A native indoor map's (BLV) baked lighting sidecar, `<map>.lighting`: lightmap pages of the static lights' direct
// light with soft shadows, their bounce and the sector ambient floor, in the indoor renderer's lighting units (the
// multiplier on the texture colour). Format: devdocs/INDOOR_BAKED_LIGHTING.md. A map without one renders as before.
struct IndoorBakedLightingPage
{
    uint32_t width = 0;
    uint32_t height = 0;
    // RLE spans of BGRM texels (BakedLightingFormat::decodeRle), validated at load and decoded for upload.
    std::vector<uint8_t> rle;

    std::vector<uint32_t> decodePixels() const;
};

struct IndoorBakedLightingFace
{
    static constexpr uint16_t NoPage = 0xffff;

    uint16_t page = NoPage;
    // The face's plane to its page: u = dot(position, uAxis.xyz) + uAxis.w, the same for v (normalized page UV).
    std::array<float, 4> uAxis = {};
    std::array<float, 4> vAxis = {};

    bool lightmapped() const
    {
        return page != NoPage;
    }
    std::array<float, 2> uvAt(float x, float y, float z) const
    {
        return {x * uAxis[0] + y * uAxis[1] + z * uAxis[2] + uAxis[3],
            x * vAxis[0] + y * vAxis[1] + z * vAxis[2] + vAxis[3]};
    }
};

// The farthest a door may travel for the bake to lightmap its faces. A door or panel moves about its own size and keeps
// its stored pose's light wherever it goes; a mover that travels farther (a lift crossing rooms) would carry one room's
// light into another, so it keeps the vertex-lit path, whose static light follows it.
constexpr uint32_t IndoorBakedMoverMaxTravel = 1024;

// Whether the bake lightmaps a door-moved face, in the BLV's stored pose: exactly one door moves it, that door moves
// every one of its vertices (the face moves rigidly, so its lightmap can move with it) and travels at most
// IndoorBakedMoverMaxTravel. Faces that stretch as a door moves (frames, sills) and long movers stay vertex-lit.
// A rotating mover (pMover with a rotation) travels the farthest chord any of its vertices sweeps.
bool indoorMoverFaceBakeable(
    const IndoorFace &face,
    std::span<const MapDeltaDoor *const> doorsMovingFace,
    const IndoorMoverDefinition *pMover = nullptr);

// The lightmap a face draws with: its page (-1: the vertex-lit path) and the offset added to the UVs of its current
// vertex positions.
struct IndoorBakedFaceLightmap
{
    int32_t page = -1;
    std::array<float, 2> uvOffset = {};
    // A rotating mover's face (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md): its current pose back to the stored
    // pose; the UVs are the stored pose's at the moved positions. Unset for every other face.
    std::optional<IndoorRigidMotion> currentToStored;

    // The face's lightmap UV at a vertex of its current pose.
    std::array<float, 2> uvAt(const IndoorBakedLightingFace &baked, float x, float y, float z) const;
};

struct IndoorBakedLighting
{
    struct Dependency
    {
        std::string path;
        uint64_t hash = 0;
    };

    uint64_t geometryHash = 0;
    std::vector<IndoorBakedLightingPage> pages;
    // Version 2 (a map open to the sky, devdocs/INDOOR_BAKED_LIGHTING.md "Daylight pages"): per page, the share of its
    // light that is the open air's (ambient and sun at noon), the same size; `pages` then holds the rest (lamps,
    // interiors). Noon light is the sum; the renderer scales the daylight share by the time of day on the faces of
    // sectors open to the sky. Empty for version 1 (every other bake).
    std::vector<IndoorBakedLightingPage> daylightPages;
    // One per BLV face, in face order.
    std::vector<IndoorBakedLightingFace> faces;
    // Per sector: the bake's bounce and ambient floor averaged over the sector's surfaces (RGB, lighting units). Actors,
    // decorations and items, still lit by the light grid, take it as their room ambient.
    std::vector<std::array<float, 3>> sectorAmbient;
    std::vector<Dependency> dependencies;

    // The lightmap page a face's batch samples, or -1 when the face keeps the vertex-lit path: no bake, the bake is
    // switched off (`[video] lightmaps`), the face is not lightmapped (a sky face, a stretching or long mover) or
    // out of range.
    static int32_t facePage(const IndoorBakedLighting *pLighting, bool enabled, size_t faceIndex);
    // facePage for a face in its current pose. A face a door moves (moved) was baked in the BLV's stored pose
    // (storedVertices): it samples its lightmap only while its current vertices are one rigid translation of that pose,
    // with the UVs shifted back by it, so the light moves with the face; otherwise (a sidecar without mover data, a
    // stretching face) it keeps the vertex-lit path, as before.
    static IndoorBakedFaceLightmap faceLightmap(
        const IndoorBakedLighting *pLighting,
        bool enabled,
        size_t faceIndex,
        const IndoorFace &face,
        bool moved,
        std::span<const IndoorVertex> vertices,
        std::span<const IndoorVertex> storedVertices,
        const IndoorRigidMotion *pStoredToCurrent = nullptr);
    // The room ambient actors take in a sector (a scalar, as IndoorLightingFrame::sectorAmbient), or nullopt to keep
    // the sector's own.
    std::optional<float> actorAmbient(size_t sectorId) const;
};

// Validates a sidecar against the map it belongs to: magic and version, every offset, count and length, the BLV's
// content hash and face and sector counts (a bake of other geometry is stale), page references, finite mappings,
// dependency paths and the RLE spans. On failure returns nullopt with the reason; the map then renders unbaked.
std::optional<IndoorBakedLighting> loadIndoorBakedLighting(
    const std::vector<uint8_t> &lightingBytes,
    const std::vector<uint8_t> &geometryBytes,
    const IndoorMapData &indoorMapData,
    std::string &errorMessage);
}
