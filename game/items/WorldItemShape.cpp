#include "game/items/WorldItemShape.h"

#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numbers>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MinSphereRadius = 2.0f;
// Steeper ground than this (stairs under a long item, a ledge) props the item up rather than tilting it further.
constexpr float MaxRestingSlope = 0.36f;
// Pick boxes are at least this large: 40 x 40 x 24.
constexpr float MinPickHalfExtent = 20.0f;
constexpr float MinPickHeight = 24.0f;

std::array<float, 2> turned(float x, float y, float cosine, float sine)
{
    return {x * cosine - y * sine, x * sine + y * cosine};
}

// The pick box in the item's own frame: its model's box grown to the minimum size about its centre, from its underside.
std::array<float, 3> pickBoxMin(const ItemModelBinding &binding)
{
    const std::array<float, 3> &low = binding.boundsMin;
    const std::array<float, 3> &high = binding.boundsMax;
    const float halfX = std::max((high[0] - low[0]) * 0.5f, MinPickHalfExtent);
    const float halfY = std::max((high[1] - low[1]) * 0.5f, MinPickHalfExtent);
    return {(low[0] + high[0]) * 0.5f - halfX, (low[1] + high[1]) * 0.5f - halfY, low[2]};
}

std::array<float, 3> pickBoxMax(const ItemModelBinding &binding)
{
    const std::array<float, 3> &low = binding.boundsMin;
    const std::array<float, 3> &high = binding.boundsMax;
    const float halfX = std::max((high[0] - low[0]) * 0.5f, MinPickHalfExtent);
    const float halfY = std::max((high[1] - low[1]) * 0.5f, MinPickHalfExtent);
    return {(low[0] + high[0]) * 0.5f + halfX, (low[1] + high[1]) * 0.5f + halfY,
            std::max(high[2], low[2] + MinPickHeight)};
}

std::optional<float> slopeBetween(
    const std::array<std::optional<float>, WorldItemFootprintSampleCount> &heights,
    size_t lowA,
    size_t lowB,
    size_t highA,
    size_t highB,
    float distance)
{
    const auto mean = [&heights](size_t first, size_t second) -> std::optional<float>
    {
        if (heights[first] && heights[second])
        {
            return (*heights[first] + *heights[second]) * 0.5f;
        }
        return heights[first] ? heights[first] : heights[second];
    };
    const std::optional<float> low = mean(lowA, lowB);
    const std::optional<float> high = mean(highA, highB);
    if (!low || !high || distance <= 1.0f)
    {
        return std::nullopt;
    }
    return (*high - *low) / distance;
}
}

float worldItemYawRadians(uint32_t key)
{
    return float((key * 2654435761u) >> 8) / float(1u << 24) * 2.0f * std::numbers::pi_v<float>;
}

WorldItemSphereChain worldItemSphereChain(const ItemModelBinding &binding, float yawRadians)
{
    const std::array<float, 3> &low = binding.boundsMin;
    const std::array<float, 3> &high = binding.boundsMax;
    const float sizeX = high[0] - low[0];
    const float sizeY = high[1] - low[1];
    const bool alongY = sizeY >= sizeX;
    const float halfLong = std::max(alongY ? sizeY : sizeX, 0.0f) * 0.5f;
    const float halfShort = std::max(alongY ? sizeX : sizeY, 0.0f) * 0.5f;
    const float height = std::max(high[2] - low[2], 0.0f);

    WorldItemSphereChain chain;
    chain.radius = std::clamp(std::max(halfShort, height * 0.5f), MinSphereRadius, std::max(halfLong, MinSphereRadius));
    const float span = std::max(halfLong - chain.radius, 0.0f);
    chain.count = span <= chain.radius * 0.25f
        ? 1
        : std::min(WorldItemSphereChain::MaxSpheres, size_t(std::ceil(span / chain.radius)) + 1);

    const float cosine = std::cos(yawRadians);
    const float sine = std::sin(yawRadians);
    const float centerX = (low[0] + high[0]) * 0.5f;
    const float centerY = (low[1] + high[1]) * 0.5f;
    for (size_t index = 0; index < chain.count; ++index)
    {
        const float along = chain.count == 1 ? 0.0f : -span + 2.0f * span * float(index) / float(chain.count - 1);
        const std::array<float, 2> offset =
            turned(centerX + (alongY ? 0.0f : along), centerY + (alongY ? along : 0.0f), cosine, sine);
        chain.offsets[index] = {offset[0], offset[1], low[2] + chain.radius};
    }
    return chain;
}

WorldItemFootprint worldItemFootprintOffsets(const ItemModelBinding &binding, float yawRadians)
{
    const std::array<float, 3> &low = binding.boundsMin;
    const std::array<float, 3> &high = binding.boundsMax;
    const float cosine = std::cos(yawRadians);
    const float sine = std::sin(yawRadians);
    return {
        turned(low[0], low[1], cosine, sine),
        turned(high[0], low[1], cosine, sine),
        turned(high[0], high[1], cosine, sine),
        turned(low[0], high[1], cosine, sine),
        turned((low[0] + high[0]) * 0.5f, (low[1] + high[1]) * 0.5f, cosine, sine),
    };
}

WorldItemRestingPose fitWorldItemRestingPose(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<std::optional<float>, WorldItemFootprintSampleCount> &groundHeights,
    float fallbackZ)
{
    const std::array<float, 3> &low = binding.boundsMin;
    const std::array<float, 3> &high = binding.boundsMax;
    // Corners in worldItemFootprintOffsets order: (minX, minY), (maxX, minY), (maxX, maxY), (minX, maxY); then centre.
    const std::array<std::array<float, 2>, WorldItemFootprintSampleCount> local = {{
        {low[0], low[1]},
        {high[0], low[1]},
        {high[0], high[1]},
        {low[0], high[1]},
        {(low[0] + high[0]) * 0.5f, (low[1] + high[1]) * 0.5f},
    }};
    const float slopeX = std::clamp(
        slopeBetween(groundHeights, 0, 3, 1, 2, high[0] - low[0]).value_or(0.0f), -MaxRestingSlope, MaxRestingSlope);
    const float slopeY = std::clamp(
        slopeBetween(groundHeights, 0, 1, 3, 2, high[1] - low[1]).value_or(0.0f), -MaxRestingSlope, MaxRestingSlope);

    WorldItemRestingPose pose;
    std::optional<float> z;
    for (size_t index = 0; index < WorldItemFootprintSampleCount; ++index)
    {
        if (groundHeights[index])
        {
            const float required = *groundHeights[index] - slopeX * local[index][0] - slopeY * local[index][1];
            z = z ? std::max(*z, required) : required;
        }
    }
    if (!z)
    {
        pose.z = fallbackZ;
        return pose;
    }

    pose.z = *z;
    const float inverseLength = 1.0f / std::sqrt(slopeX * slopeX + slopeY * slopeY + 1.0f);
    const std::array<float, 2> normal =
        turned(-slopeX * inverseLength, -slopeY * inverseLength, std::cos(yawRadians), std::sin(yawRadians));
    pose.normal = {normal[0], normal[1], inverseLength};
    return pose;
}

WorldItemPickBoxCorners worldItemPickBoxCorners(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<float, 3> &origin)
{
    const std::array<float, 3> boxMin = pickBoxMin(binding);
    const std::array<float, 3> boxMax = pickBoxMax(binding);
    const float cosine = std::cos(yawRadians);
    const float sine = std::sin(yawRadians);
    WorldItemPickBoxCorners corners = {};
    for (size_t index = 0; index < corners.size(); ++index)
    {
        const std::array<float, 2> offset = turned(
            (index & 1) != 0 ? boxMax[0] : boxMin[0],
            (index & 2) != 0 ? boxMax[1] : boxMin[1],
            cosine,
            sine);
        corners[index] = {origin[0] + offset[0], origin[1] + offset[1],
                          origin[2] + ((index & 4) != 0 ? boxMax[2] : boxMin[2])};
    }
    return corners;
}

std::optional<float> intersectWorldItemPickBox(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<float, 3> &origin,
    const std::array<float, 3> &rayOrigin,
    const std::array<float, 3> &rayDirection)
{
    const std::array<float, 3> boxMin = pickBoxMin(binding);
    const std::array<float, 3> boxMax = pickBoxMax(binding);

    // The ray in the item's own frame: turned back by its yaw about its origin.
    const float cosine = std::cos(yawRadians);
    const float sine = std::sin(yawRadians);
    const std::array<float, 2> start = turned(rayOrigin[0] - origin[0], rayOrigin[1] - origin[1], cosine, -sine);
    const std::array<float, 2> direction = turned(rayDirection[0], rayDirection[1], cosine, -sine);
    const std::array<float, 3> localStart = {start[0], start[1], rayOrigin[2] - origin[2]};
    const std::array<float, 3> localDirection = {direction[0], direction[1], rayDirection[2]};

    float entry = 0.0f;
    float exit = std::numeric_limits<float>::max();
    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (std::abs(localDirection[axis]) <= 1.0e-6f)
        {
            if (localStart[axis] < boxMin[axis] || localStart[axis] > boxMax[axis])
            {
                return std::nullopt;
            }
            continue;
        }
        float near = (boxMin[axis] - localStart[axis]) / localDirection[axis];
        float far = (boxMax[axis] - localStart[axis]) / localDirection[axis];
        if (near > far)
        {
            std::swap(near, far);
        }
        entry = std::max(entry, near);
        exit = std::min(exit, far);
        if (entry > exit)
        {
            return std::nullopt;
        }
    }
    return entry;
}

namespace
{
using Matrix3 = std::array<std::array<float, 3>, 3>;

// The pose's rotation matrix (rows): Rz(yaw) * Rx(pitch) * Ry(roll).
Matrix3 poseMatrix(const WorldItemPose &pose)
{
    const float cy = std::cos(pose.yaw), sy = std::sin(pose.yaw);
    const float cp = std::cos(pose.pitch), sp = std::sin(pose.pitch);
    const float cr = std::cos(pose.roll), sr = std::sin(pose.roll);
    const Matrix3 z = {{{cy, -sy, 0.0f}, {sy, cy, 0.0f}, {0.0f, 0.0f, 1.0f}}};
    const Matrix3 x = {{{1.0f, 0.0f, 0.0f}, {0.0f, cp, -sp}, {0.0f, sp, cp}}};
    const Matrix3 y = {{{cr, 0.0f, sr}, {0.0f, 1.0f, 0.0f}, {-sr, 0.0f, cr}}};
    const auto multiply = [](const Matrix3 &a, const Matrix3 &b)
    {
        Matrix3 result = {};
        for (size_t row = 0; row < 3; ++row)
        {
            for (size_t column = 0; column < 3; ++column)
            {
                result[row][column] = a[row][0] * b[0][column] + a[row][1] * b[1][column] + a[row][2] * b[2][column];
            }
        }
        return result;
    };
    return multiply(multiply(z, x), y);
}

std::array<float, 3> turnedBy(const Matrix3 &m, const std::array<float, 3> &v)
{
    return {m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]};
}

std::array<float, 3> turnedBackBy(const Matrix3 &m, const std::array<float, 3> &v)
{
    return {m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2],
            m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2],
            m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2]};
}
}

std::array<float, 4> worldItemPoseRotation(const WorldItemPose &pose)
{
    const Matrix3 m = poseMatrix(pose);
    const float trace = m[0][0] + m[1][1] + m[2][2];
    if (trace > 0.0f)
    {
        const float s = std::sqrt(trace + 1.0f) * 2.0f;
        return {(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25f * s};
    }
    if (m[0][0] > m[1][1] && m[0][0] > m[2][2])
    {
        const float s = std::sqrt(1.0f + m[0][0] - m[1][1] - m[2][2]) * 2.0f;
        return {0.25f * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s};
    }
    if (m[1][1] > m[2][2])
    {
        const float s = std::sqrt(1.0f + m[1][1] - m[0][0] - m[2][2]) * 2.0f;
        return {(m[0][1] + m[1][0]) / s, 0.25f * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s};
    }
    const float s = std::sqrt(1.0f + m[2][2] - m[0][0] - m[1][1]) * 2.0f;
    return {(m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25f * s, (m[1][0] - m[0][1]) / s};
}

std::array<float, 3> turnByWorldItemPose(const WorldItemPose &pose, const std::array<float, 3> &local)
{
    return turnedBy(poseMatrix(pose), local);
}

std::array<float, 3> worldItemPosedOrigin(
    const ItemModelBinding &binding,
    const WorldItemPose &pose,
    const std::array<float, 3> &position)
{
    const Matrix3 m = poseMatrix(pose);
    float lowest = std::numeric_limits<float>::max();
    for (size_t index = 0; index < 8; ++index)
    {
        const std::array<float, 3> corner = {
            (index & 1) != 0 ? binding.boundsMax[0] : binding.boundsMin[0],
            (index & 2) != 0 ? binding.boundsMax[1] : binding.boundsMin[1],
            (index & 4) != 0 ? binding.boundsMax[2] : binding.boundsMin[2]};
        lowest = std::min(lowest, turnedBy(m, corner)[2]);
    }
    return {position[0], position[1], position[2] - lowest};
}

std::optional<float> intersectPosedWorldItemPickBox(
    const ItemModelBinding &binding,
    const WorldItemPose &pose,
    const std::array<float, 3> &position,
    const std::array<float, 3> &rayOrigin,
    const std::array<float, 3> &rayDirection)
{
    // The ray in the item's own frame: turned back by the pose about the posed origin; then the unturned box test.
    const Matrix3 m = poseMatrix(pose);
    const std::array<float, 3> origin = worldItemPosedOrigin(binding, pose, position);
    const std::array<float, 3> localStart = turnedBackBy(
        m, {rayOrigin[0] - origin[0], rayOrigin[1] - origin[1], rayOrigin[2] - origin[2]});
    const std::array<float, 3> localDirection = turnedBackBy(m, rayDirection);
    return intersectWorldItemPickBox(binding, 0.0f, {0.0f, 0.0f, 0.0f}, localStart, localDirection);
}

std::array<float, 3> reflectWorldItemVelocity(const std::array<float, 3> &velocity, const std::array<float, 3> &normal)
{
    const float speed = std::sqrt(velocity[0] * velocity[0] + velocity[1] * velocity[1] + velocity[2] * velocity[2]);
    const float normalSpeed = velocity[0] * normal[0] + velocity[1] * normal[1] + velocity[2] * normal[2];
    const float dotFix = std::max(std::abs(normalSpeed), speed / 8.0f);
    std::array<float, 3> reflected = velocity;
    reflected[0] += 2.0f * dotFix * normal[0];
    reflected[1] += 2.0f * dotFix * normal[1];

    float zFix = dotFix * normal[2];
    if (normal[2] <= 0.48828125f)
    {
        zFix *= 2.0f;
    }
    else
    {
        reflected[2] += zFix;
        zFix *= 0.48828125f;
    }
    reflected[2] += zFix;
    return reflected;
}

WorldItemSparkle worldItemSparkle(const InventoryItem &item, const ItemDefinition &definition, int value)
{
    constexpr int ValuableGold = 1000;
    constexpr int PreciousGold = 2500;
    if (definition.equipStat == "Gold")
    {
        return WorldItemSparkle::Coins;
    }
    if (item.artifactId != 0 || definition.rarity != ItemRarity::Common || item.rarity == ItemRarity::Artifact
        || item.rarity == ItemRarity::Relic)
    {
        return WorldItemSparkle::Artifact;
    }
    if (definition.value <= 0)
    {
        return WorldItemSparkle::Quest;
    }
    if (value >= PreciousGold)
    {
        return WorldItemSparkle::Precious;
    }
    return value >= ValuableGold ? WorldItemSparkle::Valuable : WorldItemSparkle::None;
}
}
