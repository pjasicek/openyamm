#include "game/outdoor/OutdoorLightingData.h"

#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<uint8_t, 8> LightingMagic = {'O', 'Y', 'M', 'L', 'I', 'T', '1', 0};
constexpr uint32_t LightingFormatVersion = 2;
constexpr uint32_t LightingHeaderSize = 96;
constexpr uint32_t PageRecordSize = 16;
constexpr uint32_t FaceRecordSize = 24;
constexpr uint32_t VertexRecordSize = 12;
constexpr uint32_t LightRecordSize = 80;
constexpr uint16_t FaceHasLightmap = 0x01;
constexpr uint16_t FaceKnownFlags = FaceHasLightmap;
constexpr uint32_t LightStaticObjectEligible = 0x04;
constexpr uint32_t LightGlobalObject = 0x20;
constexpr uint32_t LightKnownFlags = 0x3f;

uint16_t readU16(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint16_t>(bytes[offset]) | (static_cast<uint16_t>(bytes[offset + 1]) << 8);
}

uint32_t readU32(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint32_t>(bytes[offset])
        | (static_cast<uint32_t>(bytes[offset + 1]) << 8)
        | (static_cast<uint32_t>(bytes[offset + 2]) << 16)
        | (static_cast<uint32_t>(bytes[offset + 3]) << 24);
}

uint64_t readU64(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint64_t>(readU32(bytes, offset))
        | (static_cast<uint64_t>(readU32(bytes, offset + 4)) << 32);
}

float readFloat(const std::vector<uint8_t> &bytes, size_t offset)
{
    const uint32_t bits = readU32(bytes, offset);
    float value = 0.0f;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

uint64_t fnv1a64(const std::vector<uint8_t> &bytes)
{
    uint64_t value = 14695981039346656037ULL;

    for (uint8_t byte : bytes)
    {
        value ^= byte;
        value *= 1099511628211ULL;
    }

    return value;
}

size_t outdoorFaceCount(const OutdoorMapData &outdoorMapData)
{
    size_t result = 0;

    for (const OutdoorBModel &bModel : outdoorMapData.bmodels)
    {
        result += bModel.faces.size();
    }

    return result;
}

size_t outdoorFaceVertexCount(const OutdoorMapData &outdoorMapData)
{
    size_t result = 0;

    for (const OutdoorBModel &bModel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bModel.faces)
        {
            result += face.vertexIndices.size();
        }
    }

    return result;
}
}

uint64_t outdoorLightingContentHash(const std::vector<uint8_t> &bytes)
{
    return fnv1a64(bytes);
}

namespace
{
uint64_t probeCellKey(int32_t x, int32_t y)
{
    return (uint64_t(uint32_t(x)) << 32) | uint32_t(y);
}
}

void OutdoorLightingData::indexProbes()
{
    probesByCell.clear();
    for (uint32_t index = 0; index < probes.size(); ++index)
    {
        const Probe &probe = probes[index];
        const int32_t x = int32_t(std::floor(probe.position[0] / 512.0f));
        const int32_t y = int32_t(std::floor(probe.position[1] / 512.0f));
        probesByCell[probeCellKey(x, y)].push_back(index);
    }
}

std::optional<OutdoorLightingData::Probe> OutdoorLightingData::sampleProbe(
    const std::array<float, 3> &position,
    const std::function<bool(const std::array<float, 3> &)> &visible) const
{
    if (!std::all_of(position.begin(), position.end(),
            [](float value) { return std::isfinite(value) && std::abs(value) < 10000000.0f; }))
    {
        return std::nullopt;
    }
    const int32_t cellX = int32_t(std::floor(position[0] / 512.0f));
    const int32_t cellY = int32_t(std::floor(position[1] / 512.0f));
    std::array<std::pair<float, uint32_t>, 4> closest;
    closest.fill({std::numeric_limits<float>::max(), 0});
    for (int32_t y = cellY - 1; y <= cellY + 1; ++y)
    {
        for (int32_t x = cellX - 1; x <= cellX + 1; ++x)
        {
            const auto found = probesByCell.find(probeCellKey(x, y));
            if (found == probesByCell.end())
            {
                continue;
            }
            for (uint32_t index : found->second)
            {
                float distance = 0.0f;
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    const float delta = probes[index].position[axis] - position[axis];
                    distance += delta * delta;
                }
                if (distance < closest.back().first)
                {
                    closest.back() = {distance, index};
                    std::sort(closest.begin(), closest.end());
                }
            }
        }
    }
    Probe result;
    result.position = position;
    float totalWeight = 0.0f;
    for (const auto &[distance, index] : closest)
    {
        if (distance > 2048.0f * 2048.0f || !visible(probes[index].position))
        {
            continue;
        }
        const float weight = 1.0f / std::max(distance, 16.0f);
        for (size_t channel = 0; channel < 3; ++channel)
        {
            result.sun[channel] += probes[index].sun[channel] * weight;
            result.sky[channel] += probes[index].sky[channel] * weight;
        }
        totalWeight += weight;
    }
    if (totalWeight == 0.0f)
    {
        return std::nullopt;
    }
    for (size_t channel = 0; channel < 3; ++channel)
    {
        result.sun[channel] /= totalWeight;
        result.sky[channel] /= totalWeight;
    }
    return result;
}

void scaleOutdoorLightingBrightness(OutdoorLightingData &lightingData, float brightnessScale)
{
    if (lightingData.hasBakedSources() || !std::isfinite(brightnessScale)
        || brightnessScale <= 0.0f || brightnessScale == 1.0f)
    {
        return;
    }

    const auto scaledChannel = [brightnessScale](uint32_t channel)
    {
        return static_cast<uint32_t>(std::clamp(std::lround(static_cast<float>(channel) * brightnessScale), 0l, 255l));
    };

    for (OutdoorLightmapAtlasPage &page : lightingData.atlasPages)
    {
        for (uint32_t &pixelBgra : page.pixelsBgra)
        {
            const uint32_t alpha = pixelBgra & 0xff000000u;
            const uint32_t red = scaledChannel((pixelBgra >> 16) & 0xffu);
            const uint32_t green = scaledChannel((pixelBgra >> 8) & 0xffu);
            const uint32_t blue = scaledChannel(pixelBgra & 0xffu);
            pixelBgra = alpha | (red << 16) | (green << 8) | blue;
        }
    }

    for (std::vector<OutdoorBModelFaceLighting> &bModelFaces : lightingData.facesByBModel)
    {
        for (OutdoorBModelFaceLighting &face : bModelFaces)
        {
            if (face.hasLightmap)
            {
                continue;
            }

            for (OutdoorBModelLightingVertex &vertex : face.vertices)
            {
                const uint32_t alpha = vertex.staticColorAbgr & 0xff000000u;
                const uint32_t red = scaledChannel((vertex.staticColorAbgr >> 16) & 0xffu);
                const uint32_t green = scaledChannel((vertex.staticColorAbgr >> 8) & 0xffu);
                const uint32_t blue = scaledChannel(vertex.staticColorAbgr & 0xffu);
                vertex.staticColorAbgr = alpha | (red << 16) | (green << 8) | blue;
            }
        }
    }
}

bool OutdoorAuthoredLight::lightsObjects() const
{
    return (flags & 0x01) != 0;
}

bool OutdoorAuthoredLight::lightsFastObjects() const
{
    return (flags & 0x02) != 0;
}

bool OutdoorAuthoredLight::staticObjectLightEligible() const
{
    return (flags & LightStaticObjectEligible) != 0;
}

bool OutdoorAuthoredLight::globalObjectLight() const
{
    return (flags & LightGlobalObject) != 0;
}

std::optional<OutdoorLightingData> OutdoorLightingDataLoader::loadFromBytes(
    const std::vector<uint8_t> &lightingBytes,
    const std::vector<uint8_t> &geometryBytes,
    const OutdoorMapData &outdoorMapData,
    std::string &errorMessage) const
{
    if (lightingBytes.size() < LightingHeaderSize
        || !std::equal(LightingMagic.begin(), LightingMagic.end(), lightingBytes.begin()))
    {
        errorMessage = "invalid outdoor lighting data magic or truncated header";
        return std::nullopt;
    }

    const uint32_t version = readU32(lightingBytes, 8);
    const uint32_t headerSize = readU32(lightingBytes, 12);
    const uint64_t geometryHash = readU64(lightingBytes, 16);
    const uint32_t sourceBModelCount = readU32(lightingBytes, 24);
    const uint32_t sourceFaceCount = readU32(lightingBytes, 28);
    const uint32_t pageCount = readU32(lightingBytes, 32);
    const uint32_t faceCount = readU32(lightingBytes, 36);
    const uint32_t vertexCount = readU32(lightingBytes, 40);
    const uint32_t lightCount = readU32(lightingBytes, 44);
    const uint32_t pageRecordsOffset = readU32(lightingBytes, 48);
    const uint32_t faceRecordsOffset = readU32(lightingBytes, 52);
    const uint32_t vertexRecordsOffset = readU32(lightingBytes, 56);
    const uint32_t lightRecordsOffset = readU32(lightingBytes, 60);
    const uint32_t pixelDataOffset = readU32(lightingBytes, 64);
    const uint32_t fileSize = readU32(lightingBytes, 68);
    const uint32_t ambientColorAbgr = readU32(lightingBytes, 72);

    if ((version != 1 && version != LightingFormatVersion)
        || headerSize != LightingHeaderSize || fileSize != lightingBytes.size())
    {
        errorMessage = "unsupported outdoor lighting data header";
        return std::nullopt;
    }

    const uint64_t expectedFaceOffset = static_cast<uint64_t>(headerSize)
        + static_cast<uint64_t>(pageCount) * PageRecordSize;
    const uint64_t expectedVertexOffset = expectedFaceOffset + static_cast<uint64_t>(faceCount) * FaceRecordSize;
    const uint64_t expectedLightOffset = expectedVertexOffset + static_cast<uint64_t>(vertexCount) * VertexRecordSize;
    const uint64_t expectedPixelOffset = expectedLightOffset + static_cast<uint64_t>(lightCount) * LightRecordSize;

    if (pageRecordsOffset != headerSize
        || faceRecordsOffset != expectedFaceOffset
        || vertexRecordsOffset != expectedVertexOffset
        || lightRecordsOffset != expectedLightOffset
        || pixelDataOffset != expectedPixelOffset
        || expectedPixelOffset > lightingBytes.size())
    {
        errorMessage = "outdoor lighting data section offsets are invalid";
        return std::nullopt;
    }

    if (geometryHash != fnv1a64(geometryBytes))
    {
        errorMessage = "outdoor lighting data was cooked for different geometry";
        return std::nullopt;
    }

    if (sourceBModelCount != outdoorMapData.bmodels.size()
        || sourceFaceCount != outdoorFaceCount(outdoorMapData)
        || faceCount != sourceFaceCount
        || vertexCount != outdoorFaceVertexCount(outdoorMapData))
    {
        errorMessage = "outdoor lighting data source counts do not match geometry";
        return std::nullopt;
    }

    OutdoorLightingData result = {};
    result.formatVersion = version;
    result.geometryHash = geometryHash;
    result.ambientColorAbgr = ambientColorAbgr;
    result.atlasPages.reserve(pageCount);
    uint64_t expectedPagePixelOffset = pixelDataOffset;

    for (size_t pageIndex = 0; pageIndex < pageCount; ++pageIndex)
    {
        const size_t recordOffset = pageRecordsOffset + pageIndex * PageRecordSize;
        OutdoorLightmapAtlasPage page = {};
        page.width = readU32(lightingBytes, recordOffset);
        page.height = readU32(lightingBytes, recordOffset + 4);
        const uint32_t pagePixelOffset = readU32(lightingBytes, recordOffset + 8);
        const uint32_t pagePixelBytes = readU32(lightingBytes, recordOffset + 12);
        const uint64_t expectedPixelBytes = static_cast<uint64_t>(page.width) * page.height * sizeof(uint32_t);

        if (page.width == 0 || page.width > 8192
            || page.height == 0 || page.height > 8192
            || pagePixelOffset != expectedPagePixelOffset
            || pagePixelBytes != expectedPixelBytes
            || expectedPagePixelOffset + expectedPixelBytes > lightingBytes.size())
        {
            errorMessage = "outdoor lighting atlas page is invalid";
            return std::nullopt;
        }

        const size_t pixelCount = static_cast<size_t>(page.width) * page.height;
        page.pixelsBgra.reserve(pixelCount);
        for (size_t pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
        {
            page.pixelsBgra.push_back(readU32(lightingBytes, pagePixelOffset + pixelIndex * sizeof(uint32_t)));
        }
        expectedPagePixelOffset += expectedPixelBytes;
        result.atlasPages.push_back(std::move(page));
    }

    if (version == 1 && expectedPagePixelOffset != lightingBytes.size())
    {
        errorMessage = "outdoor lighting atlas payload does not consume the file";
        return std::nullopt;
    }

    if (version == 2)
    {
        result.terrainPageIndex = readU32(lightingBytes, 76);
        for (size_t axis = 0; axis < 4; ++axis)
        {
            result.terrainBounds[axis] = readFloat(lightingBytes, 80 + axis * 4);
        }
        if (pageCount < 2 || pageCount % 2 != 0 || pageCount > 65534
            || result.terrainPageIndex % 2 != 0 || result.terrainPageIndex >= pageCount - 1
            || !std::all_of(result.terrainBounds.begin(), result.terrainBounds.end(),
                [](float value) { return std::isfinite(value); })
            || std::abs(result.terrainBounds[2]) < 1.0f || std::abs(result.terrainBounds[3]) < 1.0f)
        {
            errorMessage = "invalid baked outdoor terrain coverage";
            return std::nullopt;
        }
        for (size_t page = 0; page < pageCount; page += 2)
        {
            if (result.atlasPages[page].width != result.atlasPages[page + 1].width
                || result.atlasPages[page].height != result.atlasPages[page + 1].height)
            {
                errorMessage = "baked outdoor sun/sky page dimensions differ";
                return std::nullopt;
            }
        }
        size_t cursor = expectedPagePixelOffset;
        if (lightingBytes.size() - cursor < 8)
        {
            errorMessage = "truncated baked outdoor extension";
            return std::nullopt;
        }
        const uint32_t probeCount = readU32(lightingBytes, cursor);
        const uint32_t dependencyCount = readU32(lightingBytes, cursor + 4);
        cursor += 8;
        if (probeCount > (lightingBytes.size() - cursor) / 36 || dependencyCount > 100000)
        {
            errorMessage = "invalid baked outdoor extension counts";
            return std::nullopt;
        }
        result.probes.reserve(probeCount);
        for (uint32_t index = 0; index < probeCount; ++index)
        {
            OutdoorLightingData::Probe probe;
            for (std::array<float, 3> *pValues : {&probe.position, &probe.sun, &probe.sky})
            {
                for (float &value : *pValues)
                {
                    value = readFloat(lightingBytes, cursor);
                    cursor += 4;
                    if (!std::isfinite(value) || std::abs(value) > 10000000.0f)
                    {
                        errorMessage = "nonfinite baked outdoor probe";
                        return std::nullopt;
                    }
                }
            }
            for (const std::array<float, 3> *pValues : {&probe.sun, &probe.sky})
            {
                if (!std::all_of(pValues->begin(), pValues->end(),
                        [](float value) { return value >= 0.0f && value <= 4.0f; }))
                {
                    errorMessage = "baked outdoor probe exceeds RGBM4 lighting range";
                    return std::nullopt;
                }
            }
            result.probes.push_back(probe);
        }
        for (uint32_t index = 0; index < dependencyCount; ++index)
        {
            if (lightingBytes.size() - cursor < 12)
            {
                errorMessage = "truncated baked outdoor dependency";
                return std::nullopt;
            }
            const uint32_t length = readU32(lightingBytes, cursor);
            const uint64_t hash = readU64(lightingBytes, cursor + 4);
            cursor += 12;
            if (length == 0 || length > 1024 || length > lightingBytes.size() - cursor)
            {
                errorMessage = "invalid baked outdoor dependency path length";
                return std::nullopt;
            }
            const std::string path(reinterpret_cast<const char *>(lightingBytes.data() + cursor), length);
            if ((!path.starts_with("worlds/") && !path.starts_with("engine/"))
                || path.find("..") != std::string::npos || path.find('\\') != std::string::npos
                || path.find('\0') != std::string::npos)
            {
                errorMessage = "invalid baked outdoor dependency path";
                return std::nullopt;
            }
            result.dependencies.push_back({path, hash});
            cursor += length;
        }
        if (cursor != lightingBytes.size() || result.dependencies.empty())
        {
            errorMessage = "invalid baked outdoor extension payload";
            return std::nullopt;
        }
    }

    result.facesByBModel.resize(outdoorMapData.bmodels.size());
    size_t faceRecordIndex = 0;
    size_t expectedVertexIndex = 0;

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];
        std::vector<OutdoorBModelFaceLighting> &faceLighting = result.facesByBModel[bModelIndex];
        faceLighting.reserve(bModel.faces.size());

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex, ++faceRecordIndex)
        {
            const size_t recordOffset = faceRecordsOffset + faceRecordIndex * FaceRecordSize;
            const uint64_t sourceKey = readU64(lightingBytes, recordOffset);
            const uint32_t storedBModelIndex = readU32(lightingBytes, recordOffset + 8);
            const uint32_t storedFaceIndex = readU32(lightingBytes, recordOffset + 12);
            const uint16_t atlasPageIndex = readU16(lightingBytes, recordOffset + 16);
            const uint16_t flags = readU16(lightingBytes, recordOffset + 18);
            const uint32_t firstVertexIndex = readU32(lightingBytes, recordOffset + 20);
            const uint64_t expectedSourceKey = (static_cast<uint64_t>(bModelIndex) << 32) | faceIndex;
            const bool hasLightmap = (flags & FaceHasLightmap) != 0;

            if (sourceKey != expectedSourceKey
                || storedBModelIndex != bModelIndex
                || storedFaceIndex != faceIndex
                || firstVertexIndex != expectedVertexIndex
                || (flags & ~FaceKnownFlags) != 0
                || (atlasPageIndex != 0xffff && atlasPageIndex >= result.atlasPages.size())
                || (hasLightmap && atlasPageIndex == 0xffff)
                || (version == 2 && hasLightmap && atlasPageIndex % 2 != 0))
            {
                errorMessage = "outdoor lighting face identity or atlas reference is invalid";
                return std::nullopt;
            }

            OutdoorBModelFaceLighting face = {};
            face.atlasPageIndex = atlasPageIndex;
            face.hasLightmap = hasLightmap;
            face.vertices.reserve(bModel.faces[faceIndex].vertexIndices.size());
            for (size_t localVertexIndex = 0;
                 localVertexIndex < bModel.faces[faceIndex].vertexIndices.size();
                 ++localVertexIndex, ++expectedVertexIndex)
            {
                const size_t vertexOffset = vertexRecordsOffset + expectedVertexIndex * VertexRecordSize;
                if (!std::isfinite(readFloat(lightingBytes, vertexOffset))
                    || !std::isfinite(readFloat(lightingBytes, vertexOffset + 4)))
                {
                    errorMessage = "nonfinite outdoor lightmap coordinates";
                    return std::nullopt;
                }
                face.vertices.push_back({
                    readFloat(lightingBytes, vertexOffset),
                    readFloat(lightingBytes, vertexOffset + 4),
                    readU32(lightingBytes, vertexOffset + 8),
                });
            }
            faceLighting.push_back(std::move(face));
        }
    }

    result.authoredLights.reserve(lightCount);
    for (size_t lightIndex = 0; lightIndex < lightCount; ++lightIndex)
    {
        const size_t recordOffset = lightRecordsOffset + lightIndex * LightRecordSize;
        const uint32_t type = readU32(lightingBytes, recordOffset + 4);
        const uint32_t flags = readU32(lightingBytes, recordOffset + 28);
        const uint32_t reserved0 = readU32(lightingBytes, recordOffset + 68);
        const uint32_t reserved1 = readU32(lightingBytes, recordOffset + 72);
        const uint32_t reserved2 = readU32(lightingBytes, recordOffset + 76);

        if (type > static_cast<uint32_t>(OutdoorAuthoredLightType::Directional)
            || (flags & ~LightKnownFlags) != 0
            || ((flags & LightGlobalObject) != 0
                && type != static_cast<uint32_t>(OutdoorAuthoredLightType::Directional))
            || ((flags & LightGlobalObject) != 0 && (flags & LightStaticObjectEligible) != 0)
            || reserved0 != 0
            || reserved1 != 0
            || reserved2 != 0)
        {
            errorMessage = "outdoor authored light record is invalid";
            return std::nullopt;
        }

        OutdoorAuthoredLight light = {};
        light.sourceObjectIndex = readU32(lightingBytes, recordOffset);
        light.type = static_cast<OutdoorAuthoredLightType>(type);
        light.position = {
            readFloat(lightingBytes, recordOffset + 8),
            readFloat(lightingBytes, recordOffset + 12),
            readFloat(lightingBytes, recordOffset + 16),
        };
        light.radius = readFloat(lightingBytes, recordOffset + 20);
        light.effectiveColorAbgr = readU32(lightingBytes, recordOffset + 24);
        light.flags = flags;
        light.sourceRotationLt = {
            readFloat(lightingBytes, recordOffset + 32),
            readFloat(lightingBytes, recordOffset + 36),
            readFloat(lightingBytes, recordOffset + 40),
            readFloat(lightingBytes, recordOffset + 44),
        };
        light.fovDegrees = readFloat(lightingBytes, recordOffset + 48);
        light.brightnessScale = readFloat(lightingBytes, recordOffset + 52);
        light.objectBrightnessScale = readFloat(lightingBytes, recordOffset + 56);
        light.sourceColorAbgr = readU32(lightingBytes, recordOffset + 60);
        light.lightGroupCrc32 = readU32(lightingBytes, recordOffset + 64);
        result.authoredLights.push_back(light);
    }

    result.indexProbes();
    return result;
}
}
