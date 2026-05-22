#pragma once

#include "game/render/lighting/RenderLight.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct FxLightClusterConfig
{
    float cellSize = 256.0f;
    uint32_t thresholdPerSector = 8;
    uint32_t maxClustersPerSector = 8;
    float maxRadius = 900.0f;
    float maxIntensity = 2.5f;
    bool allowSectorlessLights = false;
};

struct FxLightClusterResult
{
    std::vector<RenderLight> lights;
    uint32_t clusteredInputLights = 0;
    uint32_t outputClusterLights = 0;
};

namespace FxLightClustering
{
namespace Detail
{
struct ClusterKey
{
    int16_t sectorId = -1;
    int32_t bucketX = 0;
    int32_t bucketY = 0;
    int32_t bucketZ = 0;
    RenderLightKind kind = RenderLightKind::GenericFx;
    uint32_t colorBucket = 0;

    bool operator==(const ClusterKey &other) const
    {
        return sectorId == other.sectorId
            && bucketX == other.bucketX
            && bucketY == other.bucketY
            && bucketZ == other.bucketZ
            && kind == other.kind
            && colorBucket == other.colorBucket;
    }
};

struct ClusterKeyHash
{
    size_t operator()(const ClusterKey &key) const
    {
        uint32_t hash = static_cast<uint32_t>(static_cast<uint16_t>(key.sectorId)) * 2246822519u;
        hash ^= static_cast<uint32_t>(key.bucketX) * 3266489917u;
        hash ^= static_cast<uint32_t>(key.bucketY) * 668265263u;
        hash ^= static_cast<uint32_t>(key.bucketZ) * 374761393u;
        hash ^= static_cast<uint32_t>(key.kind) * 2654435761u;
        hash ^= key.colorBucket * 362437u;
        return static_cast<size_t>(hash);
    }
};

struct ClusterAccumulation
{
    bx::Vec3 weightedPosition = {0.0f, 0.0f, 0.0f};
    float totalWeight = 0.0f;
    float energyRed = 0.0f;
    float energyGreen = 0.0f;
    float energyBlue = 0.0f;
    float maxRadius = 0.0f;
    bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
    uint32_t count = 0;
};

inline float channel(uint32_t colorAbgr, uint32_t shift)
{
    return static_cast<float>((colorAbgr >> shift) & 0xffu) / 255.0f;
}

inline uint8_t byteChannel(uint32_t colorAbgr, uint32_t shift)
{
    return static_cast<uint8_t>((colorAbgr >> shift) & 0xffu);
}

inline uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

inline bool isClusterableKind(RenderLightKind kind)
{
    return kind == RenderLightKind::Projectile
        || kind == RenderLightKind::Impact
        || kind == RenderLightKind::GenericFx;
}

inline bool isClusterableLight(const RenderLight &light, const FxLightClusterConfig &config)
{
    return light.dynamic
        && !light.important
        && (light.sectorId >= 0 || config.allowSectorlessLights)
        && light.radius > 0.0f
        && light.intensity > 0.0f
        && isClusterableKind(light.kind);
}

inline int32_t bucketCoordinate(float value, float cellSize)
{
    return static_cast<int32_t>(std::floor(value / std::max(cellSize, 1.0f)));
}

inline uint32_t colorBucket(uint32_t colorAbgr)
{
    const uint32_t red = static_cast<uint32_t>(byteChannel(colorAbgr, 0) >> 5);
    const uint32_t green = static_cast<uint32_t>(byteChannel(colorAbgr, 8) >> 5);
    const uint32_t blue = static_cast<uint32_t>(byteChannel(colorAbgr, 16) >> 5);
    return red | (green << 3) | (blue << 6);
}

inline ClusterKey makeClusterKey(const RenderLight &light, const FxLightClusterConfig &config)
{
    ClusterKey key = {};
    key.sectorId = light.sectorId;
    key.bucketX = bucketCoordinate(light.position.x, config.cellSize);
    key.bucketY = bucketCoordinate(light.position.y, config.cellSize);
    key.bucketZ = bucketCoordinate(light.position.z, config.cellSize);
    key.kind = light.kind;
    key.colorBucket = colorBucket(light.colorAbgr);
    return key;
}

inline uint32_t stableClusterId(const ClusterKey &key)
{
    return static_cast<uint32_t>(ClusterKeyHash{}(key));
}

inline float distanceSquared(const bx::Vec3 &left, const bx::Vec3 &right)
{
    const float dx = left.x - right.x;
    const float dy = left.y - right.y;
    const float dz = left.z - right.z;
    return dx * dx + dy * dy + dz * dz;
}

inline float farthestBoundsDistance(const bx::Vec3 &center, const bx::Vec3 &boundsMin, const bx::Vec3 &boundsMax)
{
    float farthestSquared = 0.0f;

    for (uint32_t corner = 0; corner < 8; ++corner)
    {
        const bx::Vec3 point = {
            (corner & 1u) != 0 ? boundsMax.x : boundsMin.x,
            (corner & 2u) != 0 ? boundsMax.y : boundsMin.y,
            (corner & 4u) != 0 ? boundsMax.z : boundsMin.z
        };
        farthestSquared = std::max(farthestSquared, distanceSquared(center, point));
    }

    return std::sqrt(farthestSquared);
}

inline uint8_t normalizedColorChannel(float energy, float maxEnergy)
{
    if (maxEnergy <= 0.0001f)
    {
        return 255;
    }

    return static_cast<uint8_t>(std::clamp(std::lround(energy / maxEnergy * 255.0f), 0l, 255l));
}

inline RenderLight finalizeCluster(
    const ClusterKey &key,
    const ClusterAccumulation &cluster,
    const FxLightClusterConfig &config)
{
    const float inverseWeight = cluster.totalWeight > 0.0001f ? 1.0f / cluster.totalWeight : 0.0f;
    const bx::Vec3 center = {
        cluster.weightedPosition.x * inverseWeight,
        cluster.weightedPosition.y * inverseWeight,
        cluster.weightedPosition.z * inverseWeight
    };
    const float boundsRadius = farthestBoundsDistance(center, cluster.boundsMin, cluster.boundsMax);
    const float maxEnergy = std::max(cluster.energyRed, std::max(cluster.energyGreen, cluster.energyBlue));

    RenderLight light = {};
    light.position = center;
    light.radius = std::min(config.maxRadius, boundsRadius + cluster.maxRadius);
    light.colorAbgr = makeAbgr(
        normalizedColorChannel(cluster.energyRed, maxEnergy),
        normalizedColorChannel(cluster.energyGreen, maxEnergy),
        normalizedColorChannel(cluster.energyBlue, maxEnergy),
        255);
    light.intensity = std::min(config.maxIntensity, std::sqrt(std::max(maxEnergy, 0.0f)));
    light.sectorId = key.sectorId;
    light.kind = RenderLightKind::ClusteredFx;
    light.stableId = stableClusterId(key);
    light.dynamic = true;
    return light;
}
}

inline FxLightClusterResult clusterSectorFxLights(
    const std::vector<RenderLight> &sourceLights,
    const FxLightClusterConfig &config)
{
    FxLightClusterResult result = {};
    result.lights.reserve(sourceLights.size());

    std::unordered_map<int16_t, uint32_t> clusterableCountsBySector;

    for (const RenderLight &light : sourceLights)
    {
        if (Detail::isClusterableLight(light, config))
        {
            ++clusterableCountsBySector[light.sectorId];
        }
    }

    std::unordered_map<Detail::ClusterKey, Detail::ClusterAccumulation, Detail::ClusterKeyHash> clusters;
    std::unordered_map<int16_t, uint32_t> outputClustersBySector;

    for (const RenderLight &light : sourceLights)
    {
        const auto sectorIterator = clusterableCountsBySector.find(light.sectorId);
        const bool sectorShouldCluster =
            sectorIterator != clusterableCountsBySector.end()
            && sectorIterator->second > config.thresholdPerSector;

        if (!sectorShouldCluster || !Detail::isClusterableLight(light, config))
        {
            result.lights.push_back(light);
            continue;
        }

        Detail::ClusterAccumulation &cluster = clusters[Detail::makeClusterKey(light, config)];
        const float alpha = Detail::channel(light.colorAbgr, 24);
        const float weight = std::max(light.intensity * alpha, 0.001f);

        if (cluster.count == 0)
        {
            cluster.boundsMin = light.position;
            cluster.boundsMax = light.position;
        }
        else
        {
            cluster.boundsMin.x = std::min(cluster.boundsMin.x, light.position.x);
            cluster.boundsMin.y = std::min(cluster.boundsMin.y, light.position.y);
            cluster.boundsMin.z = std::min(cluster.boundsMin.z, light.position.z);
            cluster.boundsMax.x = std::max(cluster.boundsMax.x, light.position.x);
            cluster.boundsMax.y = std::max(cluster.boundsMax.y, light.position.y);
            cluster.boundsMax.z = std::max(cluster.boundsMax.z, light.position.z);
        }

        cluster.weightedPosition.x += light.position.x * weight;
        cluster.weightedPosition.y += light.position.y * weight;
        cluster.weightedPosition.z += light.position.z * weight;
        cluster.totalWeight += weight;
        cluster.energyRed += Detail::channel(light.colorAbgr, 0) * alpha * light.intensity;
        cluster.energyGreen += Detail::channel(light.colorAbgr, 8) * alpha * light.intensity;
        cluster.energyBlue += Detail::channel(light.colorAbgr, 16) * alpha * light.intensity;
        cluster.maxRadius = std::max(cluster.maxRadius, light.radius);
        ++cluster.count;
        ++result.clusteredInputLights;
    }

    std::vector<std::pair<Detail::ClusterKey, Detail::ClusterAccumulation>> sortedClusters;
    sortedClusters.reserve(clusters.size());

    for (const std::pair<const Detail::ClusterKey, Detail::ClusterAccumulation> &entry : clusters)
    {
        sortedClusters.push_back({entry.first, entry.second});
    }

    std::sort(
        sortedClusters.begin(),
        sortedClusters.end(),
        [](const auto &left, const auto &right)
        {
            return left.second.totalWeight > right.second.totalWeight;
        });

    for (const std::pair<Detail::ClusterKey, Detail::ClusterAccumulation> &entry : sortedClusters)
    {
        uint32_t &outputCount = outputClustersBySector[entry.first.sectorId];

        if (outputCount >= config.maxClustersPerSector)
        {
            continue;
        }

        result.lights.push_back(Detail::finalizeCluster(entry.first, entry.second, config));
        ++outputCount;
        ++result.outputClusterLights;
    }

    return result;
}
}
}
