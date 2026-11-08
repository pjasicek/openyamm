#include "game/indoor/IndoorBakedLighting.h"

#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"
#include "game/render/lighting/BakedLightingFormat.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using BakedLightingFormat::readFloat;
using BakedLightingFormat::readU16;
using BakedLightingFormat::readU32;
using BakedLightingFormat::readU64;

constexpr std::array<uint8_t, 8> IndoorLightingMagic = {'O', 'Y', 'I', 'L', 'I', 'T', '1', 0};
constexpr uint32_t IndoorLightingVersion = 1;
// Pages in pairs: the static light, then the open air's (daylightPages).
constexpr uint32_t IndoorLightingDaylightVersion = 2;
constexpr uint32_t HeaderSize = 64;
constexpr uint32_t PageRecordSize = 16;
constexpr uint32_t FaceRecordSize = 36;
constexpr uint32_t SectorRecordSize = 12;
constexpr uint16_t FaceLightmapped = 0x01;
constexpr uint32_t MaxPageSize = 4096;
// RGBM4: decoded lighting never exceeds four.
constexpr float MaxLighting = 4.0f;
}

std::vector<uint32_t> IndoorBakedLightingPage::decodePixels() const
{
    std::vector<uint32_t> pixels;
    if (!BakedLightingFormat::decodeRle(rle, 0, rle.size(), size_t(width) * height, &pixels))
    {
        pixels.clear();
    }
    return pixels;
}

int32_t IndoorBakedLighting::facePage(const IndoorBakedLighting *pLighting, bool enabled, size_t faceIndex)
{
    if (pLighting == nullptr || !enabled || faceIndex >= pLighting->faces.size()
        || !pLighting->faces[faceIndex].lightmapped())
    {
        return -1;
    }
    return pLighting->faces[faceIndex].page;
}

IndoorBakedFaceLightmap IndoorBakedLighting::faceLightmap(
    const IndoorBakedLighting *pLighting,
    bool enabled,
    size_t faceIndex,
    const IndoorFace &face,
    bool moved,
    std::span<const IndoorVertex> vertices,
    std::span<const IndoorVertex> storedVertices,
    const IndoorRigidMotion *pStoredToCurrent)
{
    IndoorBakedFaceLightmap result;
    result.page = facePage(pLighting, enabled, faceIndex);
    if (result.page < 0 || !moved)
    {
        return result;
    }

    // A rotating mover's pose is its definition's rigid motion of the stored pose (its rounded vertices are not
    // exactly one): the lightmap is sampled at the stored positions.
    if (pStoredToCurrent != nullptr)
    {
        result.currentToStored = pStoredToCurrent->inverse();
        return result;
    }

    std::optional<std::array<int, 3>> translation;
    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size() || vertexIndex >= storedVertices.size())
        {
            return {};
        }
        const IndoorVertex &current = vertices[vertexIndex];
        const IndoorVertex &stored = storedVertices[vertexIndex];
        const std::array<int, 3> delta = {current.x - stored.x, current.y - stored.y, current.z - stored.z};
        if (translation && *translation != delta)
        {
            return {};
        }
        translation = delta;
    }
    if (!translation)
    {
        return {};
    }

    // uv(p - t) = uv(p) - (dot(t, uAxis.xyz), dot(t, vAxis.xyz)): the stored pose's texels at the moved positions.
    const IndoorBakedLightingFace &baked = pLighting->faces[faceIndex];
    const std::array<float, 3> t = {float((*translation)[0]), float((*translation)[1]), float((*translation)[2])};
    result.uvOffset = {-(t[0] * baked.uAxis[0] + t[1] * baked.uAxis[1] + t[2] * baked.uAxis[2]),
        -(t[0] * baked.vAxis[0] + t[1] * baked.vAxis[1] + t[2] * baked.vAxis[2])};
    return result;
}

std::array<float, 2> IndoorBakedFaceLightmap::uvAt(const IndoorBakedLightingFace &baked, float x, float y, float z) const
{
    if (currentToStored)
    {
        const bx::Vec3 stored = currentToStored->apply({x, y, z});
        return baked.uvAt(stored.x, stored.y, stored.z);
    }
    const std::array<float, 2> uv = baked.uvAt(x, y, z);
    return {uv[0] + uvOffset[0], uv[1] + uvOffset[1]};
}

bool indoorMoverFaceBakeable(
    const IndoorFace &face,
    std::span<const MapDeltaDoor *const> doorsMovingFace,
    const IndoorMoverDefinition *pMover)
{
    // A spinner's faces turn through every angle: its stored-pose light would turn with them (vertex-lit instead).
    if (doorsMovingFace.size() != 1 || doorsMovingFace[0] == nullptr || face.vertexIndices.size() < 3
        || (pMover != nullptr && pMover->spin))
    {
        return false;
    }
    const MapDeltaDoor &door = *doorsMovingFace[0];
    const float travel = pMover != nullptr && pMover->rotation
        ? indoorRotatingMoverMaxTravel(door, *pMover->rotation)
        : static_cast<float>(door.moveLength);
    if (travel > static_cast<float>(IndoorBakedMoverMaxTravel))
    {
        return false;
    }
    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (std::find(door.vertexIds.begin(), door.vertexIds.end(), vertexIndex) == door.vertexIds.end())
        {
            return false;
        }
    }
    return true;
}

std::optional<float> IndoorBakedLighting::actorAmbient(size_t sectorId) const
{
    if (sectorId >= sectorAmbient.size())
    {
        return std::nullopt;
    }
    const std::array<float, 3> &rgb = sectorAmbient[sectorId];
    return std::clamp((rgb[0] + rgb[1] + rgb[2]) / 3.0f, 0.0f, 1.0f);
}

std::optional<IndoorBakedLighting> loadIndoorBakedLighting(
    const std::vector<uint8_t> &bytes,
    const std::vector<uint8_t> &geometryBytes,
    const IndoorMapData &indoorMapData,
    std::string &errorMessage)
{
    const auto fail = [&errorMessage](const char *pReason) -> std::optional<IndoorBakedLighting>
    {
        errorMessage = pReason;
        return std::nullopt;
    };

    if (bytes.size() < HeaderSize || !std::equal(IndoorLightingMagic.begin(), IndoorLightingMagic.end(), bytes.begin()))
    {
        return fail("not an indoor lighting file");
    }
    const uint32_t version = readU32(bytes, 8);
    if ((version != IndoorLightingVersion && version != IndoorLightingDaylightVersion) || readU32(bytes, 12) != HeaderSize)
    {
        return fail("unsupported indoor lighting version");
    }
    const bool daylightPairs = version == IndoorLightingDaylightVersion;
    if (readU32(bytes, 60) != bytes.size())
    {
        return fail("indoor lighting length does not match the file");
    }

    IndoorBakedLighting result;
    result.geometryHash = readU64(bytes, 16);
    const uint32_t faceCount = readU32(bytes, 24);
    const uint32_t sectorCount = readU32(bytes, 28);
    const uint32_t pageCount = readU32(bytes, 32);
    const uint32_t dependencyCount = readU32(bytes, 36);
    const uint32_t pageOffset = readU32(bytes, 40);
    const uint32_t faceOffset = readU32(bytes, 44);
    const uint32_t sectorOffset = readU32(bytes, 48);
    const uint32_t dependencyOffset = readU32(bytes, 52);
    const uint32_t pixelOffset = readU32(bytes, 56);

    if (result.geometryHash != BakedLightingFormat::contentHash(geometryBytes))
    {
        return fail("baked for other geometry (stale): re-bake the map");
    }
    if (faceCount != indoorMapData.faces.size() || sectorCount != indoorMapData.sectors.size())
    {
        return fail("face or sector count does not match the map (stale): re-bake the map");
    }
    if (pageCount == 0 || pageCount >= IndoorBakedLightingFace::NoPage || dependencyCount == 0
        || dependencyCount > 100000 || (daylightPairs && pageCount % 2 != 0))
    {
        return fail("invalid indoor lighting page or dependency count");
    }
    if (pageOffset != HeaderSize
        || uint64_t(faceOffset) != uint64_t(pageOffset) + uint64_t(pageCount) * PageRecordSize
        || uint64_t(sectorOffset) != uint64_t(faceOffset) + uint64_t(faceCount) * FaceRecordSize
        || uint64_t(dependencyOffset) != uint64_t(sectorOffset) + uint64_t(sectorCount) * SectorRecordSize
        || pixelOffset < dependencyOffset || pixelOffset > bytes.size())
    {
        return fail("invalid indoor lighting section offsets");
    }

    // Pages: adjacent payloads in page order, the last ending at the file's end.
    uint64_t expectedPixelOffset = pixelOffset;
    result.pages.reserve(pageCount);
    for (uint32_t pageIndex = 0; pageIndex < pageCount; ++pageIndex)
    {
        const size_t record = pageOffset + size_t(pageIndex) * PageRecordSize;
        IndoorBakedLightingPage page;
        page.width = readU32(bytes, record);
        page.height = readU32(bytes, record + 4);
        const uint32_t payloadOffset = readU32(bytes, record + 8);
        const uint32_t payloadBytes = readU32(bytes, record + 12);
        if (page.width == 0 || page.height == 0 || page.width > MaxPageSize || page.height > MaxPageSize)
        {
            return fail("invalid indoor lighting page dimensions");
        }
        if (payloadOffset != expectedPixelOffset || payloadBytes == 0 || payloadBytes > bytes.size() - payloadOffset)
        {
            return fail("invalid indoor lighting page payload");
        }
        if (!BakedLightingFormat::decodeRle(bytes, payloadOffset, payloadBytes, size_t(page.width) * page.height,
                nullptr))
        {
            return fail("indoor lighting page compression is invalid");
        }
        page.rle.assign(bytes.begin() + payloadOffset, bytes.begin() + payloadOffset + payloadBytes);
        expectedPixelOffset = uint64_t(payloadOffset) + payloadBytes;
        if (daylightPairs && pageIndex % 2 != 0)
        {
            const IndoorBakedLightingPage &staticPage = result.pages.back();
            if (page.width != staticPage.width || page.height != staticPage.height)
            {
                return fail("indoor lighting daylight page size differs from its page");
            }
            result.daylightPages.push_back(std::move(page));
        }
        else
        {
            result.pages.push_back(std::move(page));
        }
    }
    if (expectedPixelOffset != bytes.size())
    {
        return fail("indoor lighting has trailing data");
    }

    result.faces.resize(faceCount);
    for (uint32_t faceIndex = 0; faceIndex < faceCount; ++faceIndex)
    {
        const size_t record = faceOffset + size_t(faceIndex) * FaceRecordSize;
        IndoorBakedLightingFace &face = result.faces[faceIndex];
        const uint16_t page = readU16(bytes, record);
        const uint16_t flags = readU16(bytes, record + 2);
        if ((flags & ~FaceLightmapped) != 0 || ((flags & FaceLightmapped) != 0) != (page != face.NoPage))
        {
            return fail("invalid indoor lighting face flags");
        }
        // Version 2: a face references its pair's first record.
        if (page != face.NoPage && (page >= pageCount || (daylightPairs && page % 2 != 0)))
        {
            return fail("indoor lighting face references a missing page");
        }
        face.page = page != face.NoPage && daylightPairs ? uint16_t(page / 2) : page;
        for (size_t component = 0; component < 4; ++component)
        {
            face.uAxis[component] = readFloat(bytes, record + 4 + component * 4);
            face.vAxis[component] = readFloat(bytes, record + 20 + component * 4);
            if (!std::isfinite(face.uAxis[component]) || !std::isfinite(face.vAxis[component]))
            {
                return fail("non-finite indoor lighting face mapping");
            }
        }
    }

    result.sectorAmbient.resize(sectorCount);
    for (uint32_t sectorId = 0; sectorId < sectorCount; ++sectorId)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            const float value = readFloat(bytes, sectorOffset + size_t(sectorId) * SectorRecordSize + channel * 4);
            if (!std::isfinite(value) || value < 0.0f || value > MaxLighting)
            {
                return fail("invalid indoor lighting sector ambient");
            }
            result.sectorAmbient[sectorId][channel] = value;
        }
    }

    size_t cursor = dependencyOffset;
    for (uint32_t index = 0; index < dependencyCount; ++index)
    {
        if (pixelOffset - cursor < 12)
        {
            return fail("truncated indoor lighting dependency");
        }
        const uint32_t length = readU32(bytes, cursor);
        const uint64_t hash = readU64(bytes, cursor + 4);
        cursor += 12;
        if (length == 0 || length > 1024 || length > pixelOffset - cursor)
        {
            return fail("invalid indoor lighting dependency path length");
        }
        std::string path(reinterpret_cast<const char *>(bytes.data() + cursor), length);
        if (!BakedLightingFormat::validDependencyPath(path))
        {
            return fail("invalid indoor lighting dependency path");
        }
        result.dependencies.push_back({std::move(path), hash});
        cursor += length;
    }
    if (cursor != pixelOffset)
    {
        return fail("invalid indoor lighting dependency section length");
    }

    return result;
}
}
