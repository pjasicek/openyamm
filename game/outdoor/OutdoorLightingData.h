#pragma once

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorMapData;

struct OutdoorLightmapAtlasPage
{
    uint32_t width = 0;
    uint32_t height = 0;
    std::vector<uint32_t> pixelsBgra;
};

struct OutdoorBModelLightingVertex
{
    float u = 0.5f;
    float v = 0.5f;
    uint32_t staticColorAbgr = 0xffffffff;
};

struct OutdoorBModelFaceLighting
{
    uint16_t atlasPageIndex = 0xffff;
    bool hasLightmap = false;
    std::vector<OutdoorBModelLightingVertex> vertices;
};

enum class OutdoorAuthoredLightType : uint32_t
{
    Point = 0,
    Directional = 1,
};

struct OutdoorAuthoredLight
{
    uint32_t sourceObjectIndex = 0;
    OutdoorAuthoredLightType type = OutdoorAuthoredLightType::Point;
    std::array<float, 3> position = {};
    float radius = 0.0f;
    uint32_t effectiveColorAbgr = 0xffffffff;
    uint32_t flags = 0;
    std::array<float, 4> sourceRotationLt = {};
    float fovDegrees = 90.0f;
    float brightnessScale = 1.0f;
    float objectBrightnessScale = 1.0f;
    uint32_t sourceColorAbgr = 0xffffffff;
    uint32_t lightGroupCrc32 = 0;

    bool lightsObjects() const;
    bool lightsFastObjects() const;
    bool staticObjectLightEligible() const;
    bool globalObjectLight() const;
};

struct OutdoorLightingData
{
    uint32_t formatVersion = 0;
    uint64_t geometryHash = 0;
    uint32_t ambientColorAbgr = 0xffffffff;
    std::vector<OutdoorLightmapAtlasPage> atlasPages;
    std::vector<std::vector<OutdoorBModelFaceLighting>> facesByBModel;
    std::vector<OutdoorAuthoredLight> authoredLights;
    bool bakedSourcePages = false;
    uint32_t terrainPageIndex = 0;
    std::array<float, 4> terrainBounds = {};
    struct Dependency
    {
        std::string path;
        uint64_t hash = 0;
    };
    struct Probe
    {
        std::array<float, 3> position = {};
        std::array<float, 3> sun = {};
        std::array<float, 3> sky = {};
    };
    std::vector<Dependency> dependencies;
    std::vector<Probe> probes;
    std::unordered_map<uint64_t, std::vector<uint32_t>> probesByCell;

    bool hasBakedSources() const
    {
        return bakedSourcePages;
    }
    void indexProbes();
    std::optional<Probe> sampleProbe(
        const std::array<float, 3> &position,
        const std::function<bool(const std::array<float, 3> &)> &visible) const;
};

uint64_t outdoorLightingContentHash(const std::vector<uint8_t> &bytes);

void scaleOutdoorLightingBrightness(OutdoorLightingData &lightingData, float brightnessScale);

class OutdoorLightingDataLoader
{
public:
    std::optional<OutdoorLightingData> loadFromBytes(
        const std::vector<uint8_t> &lightingBytes,
        const std::vector<uint8_t> &geometryBytes,
        const OutdoorMapData &outdoorMapData,
        std::string &errorMessage) const;
};
}
