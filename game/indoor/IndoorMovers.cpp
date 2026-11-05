#include "game/indoor/IndoorMovers.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MoverEpsilon = 1.0e-5f;

bx::Vec3 moverSub(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 moverAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 moverScale(const bx::Vec3 &value, float factor)
{
    return {value.x * factor, value.y * factor, value.z * factor};
}

float moverDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float moverLength(const bx::Vec3 &value)
{
    return std::sqrt(moverDot(value, value));
}

bx::Vec3 moverNormalized(const bx::Vec3 &value)
{
    const float valueLength = moverLength(value);
    return valueLength > MoverEpsilon ? moverScale(value, 1.0f / valueLength) : bx::Vec3{0.0f, 0.0f, 0.0f};
}

bx::Vec3 toVec(const std::array<float, 3> &value)
{
    return {value[0], value[1], value[2]};
}

bx::Vec3 polygonNormal(std::span<const bx::Vec3> polygon)
{
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const bx::Vec3 &current = polygon[index];
        const bx::Vec3 &next = polygon[(index + 1) % polygon.size()];
        normal.x += (current.y - next.y) * (current.z + next.z);
        normal.y += (current.z - next.z) * (current.x + next.x);
        normal.z += (current.x - next.x) * (current.y + next.y);
    }
    return moverNormalized(normal);
}

// Whether a point on the polygon's plane lies inside it (crossing test in the plane's dominant projection).
bool pointInsidePolygon(const bx::Vec3 &point, std::span<const bx::Vec3> polygon, const bx::Vec3 &normal)
{
    const float ax = std::fabs(normal.x);
    const float ay = std::fabs(normal.y);
    const float az = std::fabs(normal.z);
    const auto project = [&](const bx::Vec3 &value) -> std::array<float, 2>
    {
        if (az >= ax && az >= ay)
        {
            return {value.x, value.y};
        }
        if (ay >= ax)
        {
            return {value.x, value.z};
        }
        return {value.y, value.z};
    };
    const std::array<float, 2> p = project(point);
    bool inside = false;
    for (size_t index = 0, previous = polygon.size() - 1; index < polygon.size(); previous = index++)
    {
        const std::array<float, 2> a = project(polygon[index]);
        const std::array<float, 2> b = project(polygon[previous]);
        if ((a[1] > p[1]) != (b[1] > p[1]))
        {
            const float crossingX = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]);
            if (p[0] < crossingX)
            {
                inside = !inside;
            }
        }
    }
    return inside;
}

// Closest points between segments [p1, q1] and [p2, q2].
float segmentSegmentDistance(
    const bx::Vec3 &p1,
    const bx::Vec3 &q1,
    const bx::Vec3 &p2,
    const bx::Vec3 &q2,
    bx::Vec3 &closest1,
    bx::Vec3 &closest2)
{
    const bx::Vec3 d1 = moverSub(q1, p1);
    const bx::Vec3 d2 = moverSub(q2, p2);
    const bx::Vec3 r = moverSub(p1, p2);
    const float a = moverDot(d1, d1);
    const float e = moverDot(d2, d2);
    const float f = moverDot(d2, r);
    float s = 0.0f;
    float t = 0.0f;
    if (a <= MoverEpsilon && e <= MoverEpsilon)
    {
        s = 0.0f;
        t = 0.0f;
    }
    else if (a <= MoverEpsilon)
    {
        t = std::clamp(f / e, 0.0f, 1.0f);
    }
    else
    {
        const float c = moverDot(d1, r);
        if (e <= MoverEpsilon)
        {
            s = std::clamp(-c / a, 0.0f, 1.0f);
        }
        else
        {
            const float b = moverDot(d1, d2);
            const float denominator = a * e - b * b;
            s = denominator > MoverEpsilon ? std::clamp((b * f - c * e) / denominator, 0.0f, 1.0f) : 0.0f;
            t = (b * s + f) / e;
            if (t < 0.0f)
            {
                t = 0.0f;
                s = std::clamp(-c / a, 0.0f, 1.0f);
            }
            else if (t > 1.0f)
            {
                t = 1.0f;
                s = std::clamp((b - c) / a, 0.0f, 1.0f);
            }
        }
    }
    closest1 = moverAdd(p1, moverScale(d1, s));
    closest2 = moverAdd(p2, moverScale(d2, t));
    return moverLength(moverSub(closest1, closest2));
}

void bodyAxis(const IndoorMoverBody &body, bx::Vec3 &low, bx::Vec3 &high)
{
    const float lowZ = body.footZ + std::min(body.radius, body.height * 0.5f);
    const float highZ = body.footZ + std::max(body.height - body.radius, body.height * 0.5f);
    low = {body.x, body.y, lowZ};
    high = {body.x, body.y, highZ};
}
}

bx::Vec3 IndoorRigidMotion::rotate(const bx::Vec3 &direction) const
{
    return {
        rotation[0] * direction.x + rotation[1] * direction.y + rotation[2] * direction.z,
        rotation[3] * direction.x + rotation[4] * direction.y + rotation[5] * direction.z,
        rotation[6] * direction.x + rotation[7] * direction.y + rotation[8] * direction.z};
}

bx::Vec3 IndoorRigidMotion::apply(const bx::Vec3 &point) const
{
    const bx::Vec3 pivotPoint = toVec(pivot);
    return moverAdd(moverAdd(rotate(moverSub(point, pivotPoint)), pivotPoint), toVec(translation));
}

IndoorRigidMotion IndoorRigidMotion::inverse() const
{
    // p = R^T (p' - pivot - translation) + pivot: the same pivot, the transposed rotation and the translation undone.
    IndoorRigidMotion result;
    result.rotation = {rotation[0], rotation[3], rotation[6], rotation[1], rotation[4], rotation[7],
        rotation[2], rotation[5], rotation[8]};
    result.pivot = pivot;
    const bx::Vec3 undone = result.rotate(toVec(translation));
    result.translation = {-undone.x, -undone.y, -undone.z};
    return result;
}

IndoorRigidMotion composeIndoorRigidMotions(const IndoorRigidMotion &second, const IndoorRigidMotion &first)
{
    // As matrices about the origin: x -> R x + t with t = pivot - R pivot + translation.
    const auto offset = [](const IndoorRigidMotion &motion)
    {
        const bx::Vec3 pivotPoint = toVec(motion.pivot);
        return moverAdd(moverSub(pivotPoint, motion.rotate(pivotPoint)), toVec(motion.translation));
    };
    IndoorRigidMotion result;
    for (size_t row = 0; row < 3; ++row)
    {
        for (size_t column = 0; column < 3; ++column)
        {
            float value = 0.0f;
            for (size_t k = 0; k < 3; ++k)
            {
                value += second.rotation[row * 3 + k] * first.rotation[k * 3 + column];
            }
            result.rotation[row * 3 + column] = value;
        }
    }
    const bx::Vec3 combinedOffset = moverAdd(second.rotate(offset(first)), offset(second));
    result.pivot = {0.0f, 0.0f, 0.0f};
    result.translation = {combinedOffset.x, combinedOffset.y, combinedOffset.z};
    return result;
}

float indoorMoverEase(IndoorMoverEasing easing, float fraction)
{
    const float clamped = std::clamp(fraction, 0.0f, 1.0f);
    if (easing == IndoorMoverEasing::Sine)
    {
        return 0.5f - 0.5f * std::cos(clamped * bx::kPi);
    }
    return clamped;
}

float indoorMoverOpenFraction(const MapDeltaDoor &door, const IndoorMoverDefinition *pMover, float distance)
{
    if (door.moveLength == 0)
    {
        return 1.0f;
    }
    const float fraction = 1.0f - distance / static_cast<float>(door.moveLength);
    return indoorMoverEase(pMover != nullptr ? pMover->easing : IndoorMoverEasing::Linear, fraction);
}

std::optional<IndoorRigidMotion> indoorRotatingMoverMotion(
    const MapDeltaDoor &door,
    const IndoorMoverDefinition *pMover,
    float distance,
    int8_t rotationDirection)
{
    if (pMover == nullptr || !pMover->rotation)
    {
        return std::nullopt;
    }
    const IndoorMoverRotation &rotation = *pMover->rotation;
    const float sign = rotation.openAway && rotationDirection < 0 ? -1.0f : 1.0f;
    const float radians = bx::toRad(sign * rotation.openDegrees * indoorMoverOpenFraction(door, pMover, distance));
    const bx::Vec3 axis = moverNormalized(toVec(rotation.axis));
    const float c = std::cos(radians);
    const float s = std::sin(radians);
    const float t = 1.0f - c;
    IndoorRigidMotion motion;
    motion.rotation = {
        t * axis.x * axis.x + c, t * axis.x * axis.y - s * axis.z, t * axis.x * axis.z + s * axis.y,
        t * axis.x * axis.y + s * axis.z, t * axis.y * axis.y + c, t * axis.y * axis.z - s * axis.x,
        t * axis.x * axis.z - s * axis.y, t * axis.y * axis.z + s * axis.x, t * axis.z * axis.z + c};
    motion.pivot = rotation.pivot;
    return motion;
}

void applyIndoorRotatingMoverToVertices(
    const MapDeltaDoor &door,
    const IndoorRigidMotion &motion,
    std::vector<IndoorVertex> &vertices)
{
    const size_t count = std::min(
        door.vertexIds.size(),
        std::min(door.xOffsets.size(), std::min(door.yOffsets.size(), door.zOffsets.size())));
    for (size_t index = 0; index < count; ++index)
    {
        const uint16_t vertexId = door.vertexIds[index];
        if (vertexId >= vertices.size())
        {
            continue;
        }
        const bx::Vec3 moved = motion.apply({static_cast<float>(door.xOffsets[index]),
            static_cast<float>(door.yOffsets[index]), static_cast<float>(door.zOffsets[index])});
        vertices[vertexId] = {static_cast<int>(std::lround(moved.x)), static_cast<int>(std::lround(moved.y)),
            static_cast<int>(std::lround(moved.z))};
    }
}

int8_t indoorMoverOpenAwayDirection(
    const MapDeltaDoor &door,
    const IndoorMoverDefinition &mover,
    const bx::Vec3 &activator)
{
    if (!mover.rotation || door.xOffsets.empty())
    {
        return 1;
    }
    bx::Vec3 centre = {0.0f, 0.0f, 0.0f};
    for (size_t index = 0; index < door.xOffsets.size() && index < door.yOffsets.size() && index < door.zOffsets.size();
         ++index)
    {
        centre = moverAdd(centre, {static_cast<float>(door.xOffsets[index]), static_cast<float>(door.yOffsets[index]),
            static_cast<float>(door.zOffsets[index])});
    }
    centre = moverScale(centre, 1.0f / static_cast<float>(door.xOffsets.size()));
    // A little of the swing decides: the side the centre starts to move toward.
    IndoorMoverDefinition probe = mover;
    probe.easing = IndoorMoverEasing::Linear;
    probe.rotation->openAway = false;
    probe.rotation->openDegrees = std::copysign(10.0f, mover.rotation->openDegrees);
    MapDeltaDoor openDoor = door;
    openDoor.moveLength = 1;
    const std::optional<IndoorRigidMotion> motion = indoorRotatingMoverMotion(openDoor, &probe, 0.0f, 1);
    const bx::Vec3 moved = motion->apply(centre);
    const bx::Vec3 toward = moverSub(moved, centre);
    const bx::Vec3 toActivator = moverSub(activator, centre);
    const float side = toward.x * toActivator.x + toward.y * toActivator.y;
    return side > 0.0f ? int8_t(-1) : int8_t(1);
}

float indoorRotatingMoverMaxTravel(const MapDeltaDoor &door, const IndoorMoverRotation &rotation)
{
    const bx::Vec3 axis = moverNormalized(toVec(rotation.axis));
    const bx::Vec3 pivot = toVec(rotation.pivot);
    const float chord = 2.0f * std::sin(bx::toRad(std::min(std::fabs(rotation.openDegrees), 180.0f)) * 0.5f);
    float farthest = 0.0f;
    for (size_t index = 0; index < door.xOffsets.size() && index < door.yOffsets.size() && index < door.zOffsets.size();
         ++index)
    {
        const bx::Vec3 offset = moverSub({static_cast<float>(door.xOffsets[index]),
            static_cast<float>(door.yOffsets[index]), static_cast<float>(door.zOffsets[index])}, pivot);
        const float radius = moverLength(moverSub(offset, moverScale(axis, moverDot(offset, axis))));
        farthest = std::max(farthest, radius * chord);
    }
    return farthest;
}

float indoorBodyAxisPolygonDistance(
    const IndoorMoverBody &body,
    std::span<const bx::Vec3> polygon,
    bx::Vec3 *pClosestOnAxis,
    bx::Vec3 *pClosestOnPolygon)
{
    if (polygon.size() < 3)
    {
        return std::numeric_limits<float>::infinity();
    }
    bx::Vec3 low = {0.0f, 0.0f, 0.0f};
    bx::Vec3 high = {0.0f, 0.0f, 0.0f};
    bodyAxis(body, low, high);
    const bx::Vec3 normal = polygonNormal(polygon);
    float best = std::numeric_limits<float>::infinity();
    bx::Vec3 bestAxis = low;
    bx::Vec3 bestPolygon = polygon.front();
    const auto consider = [&](float distance, const bx::Vec3 &onAxis, const bx::Vec3 &onPolygon)
    {
        if (distance < best)
        {
            best = distance;
            bestAxis = onAxis;
            bestPolygon = onPolygon;
        }
    };
    if (moverLength(normal) > 0.5f)
    {
        const float lowSide = moverDot(moverSub(low, polygon.front()), normal);
        const float highSide = moverDot(moverSub(high, polygon.front()), normal);
        if ((lowSide <= 0.0f) != (highSide <= 0.0f) && std::fabs(lowSide - highSide) > MoverEpsilon)
        {
            const bx::Vec3 crossing = moverAdd(low, moverScale(moverSub(high, low), lowSide / (lowSide - highSide)));
            if (pointInsidePolygon(crossing, polygon, normal))
            {
                consider(0.0f, crossing, crossing);
            }
        }
        for (const bx::Vec3 &end : {low, high})
        {
            const float side = moverDot(moverSub(end, polygon.front()), normal);
            const bx::Vec3 projected = moverSub(end, moverScale(normal, side));
            if (pointInsidePolygon(projected, polygon, normal))
            {
                consider(std::fabs(side), end, projected);
            }
        }
    }
    for (size_t index = 0; index < polygon.size(); ++index)
    {
        bx::Vec3 onAxis = {0.0f, 0.0f, 0.0f};
        bx::Vec3 onEdge = {0.0f, 0.0f, 0.0f};
        const float distance =
            segmentSegmentDistance(low, high, polygon[index], polygon[(index + 1) % polygon.size()], onAxis, onEdge);
        consider(distance, onAxis, onEdge);
    }
    if (pClosestOnAxis != nullptr)
    {
        *pClosestOnAxis = bestAxis;
    }
    if (pClosestOnPolygon != nullptr)
    {
        *pClosestOnPolygon = bestPolygon;
    }
    return best;
}

bool indoorBodyTouchesPolygon(const IndoorMoverBody &body, std::span<const bx::Vec3> polygon)
{
    return indoorBodyAxisPolygonDistance(body, polygon) < body.radius;
}

bx::Vec3 indoorBodyPolygonClearance(
    const IndoorMoverBody &body,
    std::span<const bx::Vec3> polygon,
    const bx::Vec3 &sideHint)
{
    constexpr float Margin = 0.5f;
    constexpr int MaximumIterations = 4;
    IndoorMoverBody moved = body;
    bx::Vec3 total = {0.0f, 0.0f, 0.0f};
    const bx::Vec3 normal = polygonNormal(polygon);
    const bx::Vec3 side = moverDot(normal, sideHint) >= 0.0f ? normal : moverScale(normal, -1.0f);
    for (int iteration = 0; iteration < MaximumIterations; ++iteration)
    {
        bx::Vec3 onAxis = {0.0f, 0.0f, 0.0f};
        bx::Vec3 onPolygon = {0.0f, 0.0f, 0.0f};
        const float distance = indoorBodyAxisPolygonDistance(moved, polygon, &onAxis, &onPolygon);
        if (distance >= moved.radius)
        {
            break;
        }
        bx::Vec3 step = {0.0f, 0.0f, 0.0f};
        if (distance > 0.01f)
        {
            step = moverScale(moverNormalized(moverSub(onAxis, onPolygon)), moved.radius - distance + Margin);
        }
        else
        {
            // The polygon cuts the axis: move along the side normal until the whole axis is radius in front of it.
            bx::Vec3 low = {0.0f, 0.0f, 0.0f};
            bx::Vec3 high = {0.0f, 0.0f, 0.0f};
            bodyAxis(moved, low, high);
            const float nearest = std::min(moverDot(moverSub(low, polygon.front()), side),
                moverDot(moverSub(high, polygon.front()), side));
            step = moverScale(side, moved.radius - nearest + Margin);
        }
        moved.x += step.x;
        moved.y += step.y;
        moved.footZ += step.z;
        total = moverAdd(total, step);
    }
    return total;
}

IndoorLadderFrame indoorLadderFrame(const IndoorLadder &ladder)
{
    const float radians = bx::toRad(ladder.facingDegrees);
    IndoorLadderFrame frame;
    frame.facing = {std::cos(radians), std::sin(radians), 0.0f};
    frame.side = {-std::sin(radians), std::cos(radians), 0.0f};
    return frame;
}

bool indoorLadderGrabAllowed(const IndoorLadder &ladder, bool grounded, bool jumpRequested)
{
    return !jumpRequested && (grounded || ladder.grabInAir);
}

bool indoorLadderLeans(const IndoorLadder &ladder)
{
    const float dx = ladder.top[0] - ladder.bottom[0];
    const float dy = ladder.top[1] - ladder.bottom[1];
    return dx * dx + dy * dy > 1.0f;
}

bx::Vec3 indoorLadderLinePoint(const IndoorLadder &ladder, float footZ)
{
    const float clampedZ = std::clamp(footZ, ladder.bottom[2], ladder.top[2]);

    if (!indoorLadderLeans(ladder))
    {
        return {ladder.bottom[0], ladder.bottom[1], clampedZ};
    }

    const float fraction = (clampedZ - ladder.bottom[2]) / (ladder.top[2] - ladder.bottom[2]);
    return {
        ladder.bottom[0] + (ladder.top[0] - ladder.bottom[0]) * fraction,
        ladder.bottom[1] + (ladder.top[1] - ladder.bottom[1]) * fraction,
        clampedZ};
}

bool indoorLadderCanGrab(
    const IndoorLadder &ladder,
    const IndoorMoverBody &body,
    float desiredVelocityX,
    float desiredVelocityY)
{
    const IndoorLadderFrame frame = indoorLadderFrame(ladder);
    const bx::Vec3 line = indoorLadderLinePoint(ladder, body.footZ);
    const bx::Vec3 offset = {body.x - line.x, body.y - line.y, 0.0f};
    const float depth = moverDot(offset, frame.facing);
    const float lateral = moverDot(offset, frame.side);
    const float speed = std::sqrt(desiredVelocityX * desiredVelocityX + desiredVelocityY * desiredVelocityY);
    if (speed < 1.0f
        || (desiredVelocityX * frame.facing.x + desiredVelocityY * frame.facing.y) < 0.5f * speed)
    {
        return false;
    }
    return depth >= -(ladder.reach + body.radius)
        && depth <= body.radius
        && std::fabs(lateral) <= ladder.width * 0.5f
        && body.footZ >= ladder.bottom[2] - 24.0f
        && body.footZ <= ladder.top[2] - 8.0f;
}

bool indoorLadderCanGrabAtTop(
    const IndoorLadder &ladder,
    const IndoorMoverBody &body,
    float desiredVelocityX,
    float desiredVelocityY)
{
    if (!ladder.grabAtTop || std::fabs(body.footZ - ladder.topExit[2]) > 48.0f)
    {
        return false;
    }

    const float fromExitX = body.x - ladder.topExit[0];
    const float fromExitY = body.y - ladder.topExit[1];
    const float reach = ladder.reach + body.radius;

    if (fromExitX * fromExitX + fromExitY * fromExitY > reach * reach)
    {
        return false;
    }

    const float toTopX = ladder.top[0] - body.x;
    const float toTopY = ladder.top[1] - body.y;
    const float distance = std::sqrt(toTopX * toTopX + toTopY * toTopY);
    const float speed = std::sqrt(desiredVelocityX * desiredVelocityX + desiredVelocityY * desiredVelocityY);
    return speed >= 1.0f && distance >= 1.0f
        && (desiredVelocityX * toTopX + desiredVelocityY * toTopY) >= 0.5f * speed * distance;
}

bx::Vec3 indoorLadderTopEntryPosition(const IndoorLadder &ladder, const IndoorMoverBody &body)
{
    const IndoorLadderFrame frame = indoorLadderFrame(ladder);
    const float footZ = std::max(ladder.bottom[2], ladder.top[2] - IndoorLadderTopEntryDrop);
    const bx::Vec3 line = indoorLadderLinePoint(ladder, footZ);
    const float holdDistance = body.radius + IndoorLadderHoldGap;
    return {line.x - frame.facing.x * holdDistance, line.y - frame.facing.y * holdDistance, footZ};
}

IndoorLadderClimbStep indoorLadderClimbStep(
    const IndoorLadder &ladder,
    const IndoorMoverBody &body,
    float desiredVelocityX,
    float desiredVelocityY,
    int verticalInput,
    bool running,
    float deltaSeconds)
{
    const IndoorLadderFrame frame = indoorLadderFrame(ladder);
    const bx::Vec3 line = indoorLadderLinePoint(ladder, body.footZ);
    const bx::Vec3 offset = {body.x - line.x, body.y - line.y, 0.0f};
    const float depth = moverDot(offset, frame.facing);
    const float lateral = moverDot(offset, frame.side);
    const float speed = std::sqrt(desiredVelocityX * desiredVelocityX + desiredVelocityY * desiredVelocityY);
    const float toward = desiredVelocityX * frame.facing.x + desiredVelocityY * frame.facing.y;
    const float along = desiredVelocityX * frame.side.x + desiredVelocityY * frame.side.y;
    int climb = verticalInput;
    bool climbsByExit = false;
    if (climb == 0 && speed >= 1.0f && std::fabs(toward) >= 0.5f * speed)
    {
        climb = toward > 0.0f ? 1 : -1;
    }
    else if (climb == 0 && speed >= 1.0f && ladder.grabAtTop)
    {
        // Taken at the top from the side: walking on toward the strip goes down, walking back toward the exit goes up.
        const float exitX = ladder.topExit[0] - ladder.top[0];
        const float exitY = ladder.topExit[1] - ladder.top[1];
        const float exitLength = std::sqrt(exitX * exitX + exitY * exitY);
        const float outward = exitLength >= 1.0f
            ? (desiredVelocityX * exitX + desiredVelocityY * exitY) / exitLength : 0.0f;
        if (std::fabs(outward) >= 0.5f * speed)
        {
            climb = outward > 0.0f ? 1 : -1;
            climbsByExit = true;
        }
    }

    IndoorLadderClimbStep step;
    if (std::fabs(lateral) > ladder.width * 0.5f + body.radius)
    {
        step.detach = true;
        return step;
    }
    const float climbSpeed = running ? IndoorLadderRunClimbSpeed : IndoorLadderClimbSpeed;
    step.verticalVelocity = static_cast<float>(climb) * climbSpeed;
    if (climb > 0 && body.footZ >= ladder.top[2] - 4.0f)
    {
        step.exitTop = true;
        step.verticalVelocity = 0.0f;
        return step;
    }
    // Hold the body just in front of the strip; move along it with the strafe part of the input.
    const float targetDepth = -(body.radius + IndoorLadderHoldGap);
    const float hold = std::clamp((targetDepth - depth) / std::max(deltaSeconds, 1.0e-3f), -256.0f, 256.0f);
    const float sideways = std::fabs(toward) >= 0.5f * speed || climbsByExit
        ? 0.0f : std::clamp(along, -climbSpeed, climbSpeed);
    step.velocityX = frame.facing.x * hold + frame.side.x * sideways;
    step.velocityY = frame.facing.y * hold + frame.side.y * sideways;
    if (indoorLadderLeans(ladder))
    {
        // Follow the line: the horizontal run per unit of height times the climb's vertical speed.
        const float rise = ladder.top[2] - ladder.bottom[2];
        step.velocityX += (ladder.top[0] - ladder.bottom[0]) / rise * step.verticalVelocity;
        step.velocityY += (ladder.top[1] - ladder.bottom[1]) / rise * step.verticalVelocity;
    }
    return step;
}
}
