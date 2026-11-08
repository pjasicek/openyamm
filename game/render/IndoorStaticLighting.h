#pragma once

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
struct DecorationBillboard;
struct DecorationBillboardSet;
struct EventRuntimeState;
struct IndoorLight;
struct IndoorMapData;

struct BakedStaticLightSource
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    uint8_t red = 255;
    uint8_t green = 255;
    uint8_t blue = 255;
    float alpha = 1.0f;
    // The light's index in the renderer's enabled-state list: map lights, then decoration billboards. It selects the
    // light's reach (the sectors it may bake into).
    uint32_t sourceId = 0;
    // The open air's light (indoorOpenAirLights): its share of the static vertex light follows the daylight.
    bool openAir = false;
};

constexpr float IndoorBakedStaticLightScale = 1.35f;
// The map lights' strength (alpha) in the static light: 224 / 255.
constexpr uint8_t IndoorBakedStaticLightAlpha = 224;
constexpr float IndoorBakedStaticLightSubdivisionMinEdgeLength = 32.0f;
constexpr float IndoorBakedStaticLightInterpolationTolerance = 0.05f;

// The static light of a light-emitting decoration (its table light, or its sprite's glow), at its middle height; none
// for a decoration whose map light lights it (resolveDuplicateTorchLights). includeInactiveSources also takes the
// brighter state of a decoration that toggles.
std::optional<BakedStaticLightSource> bakedStaticLightSourceForDecoration(
    const DecorationBillboardSet &billboardSet,
    const DecorationBillboard &billboard,
    const EventRuntimeState *pEventRuntimeState,
    bool includeInactiveSources);
// The map light lightId as a static light source (its sourceId, and whether it is the open air's light).
BakedStaticLightSource bakedStaticLightSourceForIndoorLight(const IndoorMapData &indoorMapData, size_t lightId);
// Every static light of an indoor map: its map lights with a radius, then its light-emitting decorations; only those
// enabled in pEventRuntimeState unless includeInactiveSources. sourceId is the light's index in that order.
std::vector<BakedStaticLightSource> buildBakedStaticLightSources(
    const IndoorMapData &indoorMapData,
    const EventRuntimeState *pEventRuntimeState,
    const DecorationBillboardSet *pDecorationBillboardSet,
    bool includeInactiveSources);

inline float indoorBakedLightPointSegmentDistanceSquared(
    const bx::Vec3 &point,
    const bx::Vec3 &first,
    const bx::Vec3 &second)
{
    const bx::Vec3 segment = bx::sub(second, first);
    const float segmentLengthSquared = bx::dot(segment, segment);
    const float segmentProgress = segmentLengthSquared > 0.0001f
        ? std::clamp(bx::dot(bx::sub(point, first), segment) / segmentLengthSquared, 0.0f, 1.0f)
        : 0.0f;
    const bx::Vec3 closestPoint = bx::add(first, bx::mul(segment, segmentProgress));
    const bx::Vec3 delta = bx::sub(point, closestPoint);
    return bx::dot(delta, delta);
}

inline float indoorBakedLightPointTriangleDistanceSquared(
    const bx::Vec3 &point,
    const bx::Vec3 &first,
    const bx::Vec3 &second,
    const bx::Vec3 &third)
{
    const bx::Vec3 firstToSecond = bx::sub(second, first);
    const bx::Vec3 firstToThird = bx::sub(third, first);
    const bx::Vec3 normal = bx::cross(firstToSecond, firstToThird);
    const float normalLengthSquared = bx::dot(normal, normal);

    if (normalLengthSquared <= 0.0001f)
    {
        return std::min(
            indoorBakedLightPointSegmentDistanceSquared(point, first, second),
            std::min(
                indoorBakedLightPointSegmentDistanceSquared(point, second, third),
                indoorBakedLightPointSegmentDistanceSquared(point, third, first)));
    }

    const float planeProjection = bx::dot(bx::sub(point, first), normal);
    const bx::Vec3 projectedPoint = bx::sub(point, bx::mul(normal, planeProjection / normalLengthSquared));
    const bool insideTriangle =
        bx::dot(bx::cross(firstToSecond, bx::sub(projectedPoint, first)), normal) >= -0.0001f
        && bx::dot(bx::cross(bx::sub(third, second), bx::sub(projectedPoint, second)), normal) >= -0.0001f
        && bx::dot(bx::cross(bx::sub(first, third), bx::sub(projectedPoint, third)), normal) >= -0.0001f;

    if (insideTriangle)
    {
        return planeProjection * planeProjection / normalLengthSquared;
    }

    return std::min(
        indoorBakedLightPointSegmentDistanceSquared(point, first, second),
        std::min(
            indoorBakedLightPointSegmentDistanceSquared(point, second, third),
            indoorBakedLightPointSegmentDistanceSquared(point, third, first)));
}

inline bool indoorBakedStaticLightNeedsSubdivision(
    std::span<const BakedStaticLightSource> bakedStaticLightSources,
    const std::array<bx::Vec3, 3> &trianglePositions)
{
    const std::array<bx::Vec3, 4> samplePositions = {
        bx::mul(bx::add(trianglePositions[0], trianglePositions[1]), 0.5f),
        bx::mul(bx::add(trianglePositions[1], trianglePositions[2]), 0.5f),
        bx::mul(bx::add(trianglePositions[2], trianglePositions[0]), 0.5f),
        bx::mul(bx::add(bx::add(trianglePositions[0], trianglePositions[1]), trianglePositions[2]), 1.0f / 3.0f)
    };
    std::array<float, 4> interpolationErrors = {};
    for (const BakedStaticLightSource &source : bakedStaticLightSources)
    {
        if (source.radius <= 0.0f || source.alpha <= 0.0f)
        {
            continue;
        }

        const float radiusSquared = source.radius * source.radius;
        const float triangleDistanceSquared = indoorBakedLightPointTriangleDistanceSquared(
            source.position, trianglePositions[0], trianglePositions[1], trianglePositions[2]);
        if (triangleDistanceSquared >= radiusSquared)
        {
            continue;
        }

        const float brightness = static_cast<float>(std::max({source.red, source.green, source.blue})) / 255.0f;
        const float scale = IndoorBakedStaticLightScale * source.alpha * brightness;
        const float nearestAttenuation = 1.0f - triangleDistanceSquared / radiusSquared;
        const auto attenuationAt = [&](const bx::Vec3 &position)
        {
            const bx::Vec3 delta = bx::sub(position, source.position);
            const float attenuation = std::max(0.0f, 1.0f - bx::dot(delta, delta) / radiusSquared);
            return attenuation * attenuation;
        };
        const float first = attenuationAt(trianglePositions[0]);
        const float second = attenuationAt(trianglePositions[1]);
        const float third = attenuationAt(trianglePositions[2]);
        const std::array<float, 4> interpolated = {
            (first + second) * 0.5f, (second + third) * 0.5f, (third + first) * 0.5f,
            (first + second + third) / 3.0f
        };
        std::array<float, 4> sourceErrors = {};
        float maximumSampled = std::max({first, second, third});
        for (size_t sample = 0; sample < samplePositions.size(); ++sample)
        {
            const float sampled = attenuationAt(samplePositions[sample]);
            maximumSampled = std::max(maximumSampled, sampled);
            sourceErrors[sample] = std::abs(sampled - interpolated[sample]);
        }
        // A glow entirely between the probes still needs discovery. Use its nearest-point bound while probes are dim.
        if (maximumSampled * scale <= IndoorBakedStaticLightInterpolationTolerance)
        {
            for (float &sourceError : sourceErrors)
            {
                sourceError = std::max(sourceError, nearestAttenuation * nearestAttenuation - maximumSampled);
            }
        }
        // Bound each probe separately, without cancellation, so toggling lights retains the same error budget.
        for (size_t sample = 0; sample < interpolationErrors.size(); ++sample)
        {
            interpolationErrors[sample] += sourceErrors[sample] * scale;
            if (interpolationErrors[sample] > IndoorBakedStaticLightInterpolationTolerance)
            {
                return true;
            }
        }
    }

    return false;
}
}
