#include "game/indoor/IndoorWater.h"

#include "game/indoor/IndoorMapData.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
float topOffset(std::span<const float> topOffsets, size_t volumeIndex)
{
    return volumeIndex < topOffsets.size() ? topOffsets[volumeIndex] : 0.0f;
}

bool boundsContain(const IndoorWaterPiece &piece, float x, float y)
{
    return x >= piece.bounds[0] && y >= piece.bounds[1] && x <= piece.bounds[2] && y <= piece.bounds[3];
}
}

std::array<float, 3> indoorLiquidDefaultTint(IndoorLiquid liquid)
{
    return liquid == IndoorLiquid::Lava ? std::array<float, 3>{0.5f, 0.15f, 0.0f}
                                        : std::array<float, 3>{0.0f, 0.5f, 0.7f};
}

void finalizeIndoorWaterPiece(IndoorWaterPiece &piece)
{
    if (piece.polygon.empty())
    {
        piece.bounds = {0.0f, 0.0f, 0.0f, 0.0f};
        return;
    }

    piece.bounds = {piece.polygon[0][0], piece.polygon[0][1], piece.polygon[0][0], piece.polygon[0][1]};

    for (const std::array<float, 2> &point : piece.polygon)
    {
        piece.bounds[0] = std::min(piece.bounds[0], point[0]);
        piece.bounds[1] = std::min(piece.bounds[1], point[1]);
        piece.bounds[2] = std::max(piece.bounds[2], point[0]);
        piece.bounds[3] = std::max(piece.bounds[3], point[1]);
    }
}

bool indoorWaterPieceContains(const IndoorWaterPiece &piece, float x, float y)
{
    if (piece.polygon.size() < 3 || !boundsContain(piece, x, y))
    {
        return false;
    }

    // Even-odd crossing test: either winding, convex or not.
    bool inside = false;
    const size_t count = piece.polygon.size();

    for (size_t index = 0, previous = count - 1; index < count; previous = index++)
    {
        const std::array<float, 2> &a = piece.polygon[index];
        const std::array<float, 2> &b = piece.polygon[previous];

        if ((a[1] > y) != (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0])
        {
            inside = !inside;
        }
    }

    return inside;
}

std::vector<float> indoorWaterTopOffsets(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const IndoorVertex> storedVertices,
    std::span<const IndoorVertex> runtimeVertices)
{
    std::vector<float> offsets(volumes.size(), 0.0f);

    for (size_t index = 0; index < volumes.size(); ++index)
    {
        const std::optional<uint16_t> vertexId = volumes[index].moverVertexId;

        if (vertexId && *vertexId < storedVertices.size() && *vertexId < runtimeVertices.size())
        {
            offsets[index] = static_cast<float>(runtimeVertices[*vertexId].z - storedVertices[*vertexId].z);
        }
    }

    return offsets;
}

std::optional<IndoorWaterSample> indoorWaterAt(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    float x,
    float y,
    float z)
{
    for (size_t volumeIndex = 0; volumeIndex < volumes.size(); ++volumeIndex)
    {
        const float offset = topOffset(topOffsets, volumeIndex);

        for (const IndoorWaterPiece &piece : volumes[volumeIndex].pieces)
        {
            const float top = piece.top + offset;

            if (z >= piece.bottom && z < top && indoorWaterPieceContains(piece, x, y))
            {
                return IndoorWaterSample{volumeIndex, top, piece.bottom};
            }
        }
    }

    return std::nullopt;
}

std::optional<IndoorWaterSample> indoorBodyWaterSample(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    float x,
    float y,
    float footZ,
    float height)
{
    std::optional<IndoorWaterSample> best;

    for (size_t volumeIndex = 0; volumeIndex < volumes.size(); ++volumeIndex)
    {
        const float offset = topOffset(topOffsets, volumeIndex);

        for (const IndoorWaterPiece &piece : volumes[volumeIndex].pieces)
        {
            const float top = piece.top + offset;

            if (top <= piece.bottom || footZ >= top || footZ + height < piece.bottom
                || !indoorWaterPieceContains(piece, x, y))
            {
                continue;
            }

            if (!best || top > best->surfaceZ)
            {
                best = IndoorWaterSample{volumeIndex, top, piece.bottom};
            }
        }
    }

    return best;
}

std::optional<IndoorWaterSample> indoorWaterVolumeColumn(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    size_t volumeIndex,
    float x,
    float y)
{
    if (volumeIndex >= volumes.size())
    {
        return std::nullopt;
    }

    const float offset = topOffset(topOffsets, volumeIndex);

    for (const IndoorWaterPiece &piece : volumes[volumeIndex].pieces)
    {
        if (piece.top + offset > piece.bottom && indoorWaterPieceContains(piece, x, y))
        {
            return IndoorWaterSample{volumeIndex, piece.top + offset, piece.bottom};
        }
    }

    return std::nullopt;
}

const char *indoorSwimStateName(IndoorSwimState state)
{
    switch (state)
    {
        case IndoorSwimState::Dry:
            return "dry";
        case IndoorSwimState::Wading:
            return "wading";
        case IndoorSwimState::Falling:
            return "falling";
        case IndoorSwimState::Bed:
            return "bed";
        case IndoorSwimState::Submerged:
            return "submerged";
        case IndoorSwimState::Surface:
            return "surface";
        case IndoorSwimState::SurfaceJump:
            return "surface_jump";
    }

    return "unknown";
}

IndoorSwimState indoorSwimState(const IndoorSwimFacts &facts, IndoorSwimMemory &memory)
{
    if (!facts.bodyInWater)
    {
        memory = {};
        return IndoorSwimState::Dry;
    }

    if (facts.eyeUnder)
    {
        memory.wasSubmerged = true;
        memory.surfaceJump = false;
        // MM9 takes WalkingInWater (the land mover) before UnderWater: on the bed the party walks.
        return facts.grounded ? IndoorSwimState::Bed : IndoorSwimState::Submerged;
    }

    if (facts.grounded)
    {
        // Feet on a floor with the eye out: wading, also out of a surface jump that landed. MM9 keeps its surface
        // mover over a shallow floor and lets the collision lift the body; ours walks out instead (design deviation).
        memory.surfaceJump = false;
        return IndoorSwimState::Wading;
    }

    if (memory.surfaceJump)
    {
        return IndoorSwimState::SurfaceJump;
    }

    return memory.wasSubmerged ? IndoorSwimState::Surface : IndoorSwimState::Falling;
}

IndoorSwimVelocity indoorSwimVelocity(
    IndoorSwimState state,
    const IndoorSwimInput &input,
    float speedMultiplier,
    float eyePointOverSurface,
    float deltaSeconds)
{
    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const float cosPitch = std::cos(input.pitchRadians);
    float sinPitch = std::sin(input.pitchRadians);
    const bool surface = state == IndoorSwimState::Surface;

    if (surface)
    {
        // The camera's vectors with their upward part removed (cshell 0x10095bb0): looking down dives.
        sinPitch = std::min(sinPitch, 0.0f);
    }

    const float forward = std::clamp(input.forward, -1.0f, 1.0f);
    const float strafe = std::clamp(input.strafe, -1.0f, 1.0f);
    // On the surface only Fly Down (MM9's Crouch) moves vertically: down.
    const float vertical = surface ? std::min(0.0f, float(input.vertical)) : float(std::clamp(input.vertical, -1, 1));
    float wishX = cosYaw * cosPitch * forward + sinYaw * strafe;
    float wishY = sinYaw * cosPitch * forward - cosYaw * strafe;
    float wishZ = sinPitch * forward + vertical;
    const float length = std::sqrt(wishX * wishX + wishY * wishY + wishZ * wishZ);

    if (length > 1.0f)
    {
        wishX /= length;
        wishY /= length;
        wishZ /= length;
    }

    const float speed = IndoorSwimSpeed * std::max(0.0f, speedMultiplier) * std::clamp(input.speedScale, 0.0f, 16.0f);
    IndoorSwimVelocity velocity = {wishX * speed, wishY * speed, wishZ * speed};
    const bool anyInput = forward != 0.0f || strafe != 0.0f || input.vertical != 0;

    if (state == IndoorSwimState::Submerged && !anyInput)
    {
        velocity.z = -IndoorSwimIdleSinkSpeed;
    }

    if (surface && velocity.z >= 0.0f && deltaSeconds > 0.0f)
    {
        // Held at the surface pose: the eye point IndoorSwimSurfaceHold over the water, no drift.
        velocity.z = std::clamp(
            (IndoorSwimSurfaceHold - eyePointOverSurface) / deltaSeconds, -IndoorSwimSpeed, IndoorSwimSpeed);
    }

    return velocity;
}

IndoorSwimVelocity indoorSurfaceJumpAirControl(const IndoorSwimInput &input, float speedMultiplier)
{
    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const float forward = std::clamp(input.forward, -1.0f, 1.0f);
    const float strafe = std::clamp(input.strafe, -1.0f, 1.0f);
    const float scale = std::max(0.0f, speedMultiplier) * std::clamp(input.speedScale, 0.0f, 16.0f);
    const float forwardSpeed = (forward > 0.0f ? IndoorSurfaceJumpForwardSpeed : IndoorSurfaceJumpSideSpeed) * forward;
    const float strafeSpeed = IndoorSurfaceJumpSideSpeed * strafe;
    return {
        (cosYaw * forwardSpeed + sinYaw * strafeSpeed) * scale,
        (sinYaw * forwardSpeed - cosYaw * strafeSpeed) * scale,
        0.0f};
}

uint32_t advanceIndoorBreath(IndoorBreathState &breath, bool eyeUnder, float deltaSeconds)
{
    if (!eyeUnder)
    {
        breath = {};
        return 0;
    }

    breath.underSeconds += std::max(0.0f, deltaSeconds);
    uint32_t ticks = 0;

    // MM9: when more than 15 s have passed since the last breath, a tick, and the last breath moves on by 2 s.
    while (breath.underSeconds >= breath.nextTickSeconds)
    {
        ++ticks;
        breath.nextTickSeconds += IndoorDrowningTickSeconds;
    }

    return ticks;
}

float indoorBreathFraction(const IndoorBreathState &breath)
{
    return std::clamp(1.0f - breath.underSeconds / IndoorBreathSeconds, 0.0f, 1.0f);
}

int indoorDrowningDamage(int maxHealth)
{
    return std::max(1, maxHealth / IndoorDrowningMaxHealthDivisor);
}
}
