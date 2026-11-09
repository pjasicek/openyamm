#pragma once

#include "game/tables/ItemModelBindings.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
struct InventoryItem;
struct ItemDefinition;

// How an item lies on the ground and collides (GROUND_ITEMS_3D_BEHAVIOUR.md): its model's box turned by a yaw of its
// own. Shared by both world runtimes (physics), the presentation and the picking.

// The yaw an item lies at, from the world's key for it (outdoors its world item id, indoors its map object index), so
// neighbouring items do not all point the same way.
float worldItemYawRadians(uint32_t key);

// The spheres an airborne item sweeps against walls and ceilings: one for a compact item, up to five spaced along the
// long side of a long one, each resting on the item's underside. Offsets are from the item's origin, turned by its
// yaw. Floors are left to the world's floor query.
struct WorldItemSphereChain
{
    static constexpr size_t MaxSpheres = 5;
    std::array<std::array<float, 3>, MaxSpheres> offsets = {};
    size_t count = 0;
    float radius = 0.0f;
};
WorldItemSphereChain worldItemSphereChain(const ItemModelBinding &binding, float yawRadians);

// The points under an item's footprint where its resting pose samples the ground: the four corners of its box and its
// centre, as world offsets from its origin turned by its yaw.
constexpr size_t WorldItemFootprintSampleCount = 5;
using WorldItemFootprint = std::array<std::array<float, 2>, WorldItemFootprintSampleCount>;
WorldItemFootprint worldItemFootprintOffsets(const ItemModelBinding &binding, float yawRadians);

// A settled item's pose: the height of its origin and the up axis it is tilted to.
struct WorldItemRestingPose
{
    float z = 0.0f;
    std::array<float, 3> normal = {0.0f, 0.0f, 1.0f};
};
// Fits an item to the ground heights under its footprint (in worldItemFootprintOffsets order; nullopt where nothing
// supports it): tilted to the slope along and across the item, at most a fixed angle, then raised so no supporting
// point is above its underside. With no support it lies flat at fallbackZ.
WorldItemRestingPose fitWorldItemRestingPose(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<std::optional<float>, WorldItemFootprintSampleCount> &groundHeights,
    float fallbackZ);

// Where a ray (unit direction) enters the box an item is picked with: its model's box grown to a minimum size, so small
// items stay easy to click, turned by its yaw. The distance along the ray, or nullopt.
std::optional<float> intersectWorldItemPickBox(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<float, 3> &origin,
    const std::array<float, 3> &rayOrigin,
    const std::array<float, 3> &rayDirection);

// The eight world corners of that pick box for an item at origin (bit 0: high x, bit 1: high y, bit 2: top), for
// targets chosen on screen rather than along a ray.
using WorldItemPickBoxCorners = std::array<std::array<float, 3>, 8>;
WorldItemPickBoxCorners worldItemPickBoxCorners(
    const ItemModelBinding &binding,
    float yawRadians,
    const std::array<float, 3> &origin);

// An authored pose for a placed item (a scene's world item `pose`: a shield leaning on a wall): turned by yaw about the
// world's up axis, then pitch about its own x (across) axis, then roll about its own y (along) axis, radians. A posed
// item rests with the lowest point of its turned box at its position; it is never fitted to the ground.
struct WorldItemPose
{
    float yaw = 0.0f;
    float pitch = 0.0f;
    float roll = 0.0f;
};
// The pose's rotation as a quaternion (x, y, z, w).
std::array<float, 4> worldItemPoseRotation(const WorldItemPose &pose);
// A point of the item's own frame turned by the pose (an offset from the posed origin).
std::array<float, 3> turnByWorldItemPose(const WorldItemPose &pose, const std::array<float, 3> &local);
// Where the posed model's origin goes for an item at position: raised so the turned box's lowest point is there.
std::array<float, 3> worldItemPosedOrigin(
    const ItemModelBinding &binding,
    const WorldItemPose &pose,
    const std::array<float, 3> &position);
// intersectWorldItemPickBox for a posed item at position: the pick box turned by the whole pose.
std::optional<float> intersectPosedWorldItemPickBox(
    const ItemModelBinding &binding,
    const WorldItemPose &pose,
    const std::array<float, 3> &position,
    const std::array<float, 3> &rayOrigin,
    const std::array<float, 3> &rayDirection);

// An item's velocity after it strikes a wall or ceiling with the given unit normal (facing the item): the normal part
// reflected, at least an eighth of its speed, as the native object bounce does; damping is the caller's.
std::array<float, 3> reflectWorldItemVelocity(const std::array<float, 3> &velocity, const std::array<float, 3> &normal);

// How an item on the ground sparkles: by its value in gold (with its enchantments, as a shop buys it), artifacts, relics
// and named uniques in gold, quest items (worth nothing) in red, coin heaps in white.
enum class WorldItemSparkle : uint8_t
{
    None = 0,
    Valuable,   // 1000 gold or more
    Precious,   // 2500 gold or more
    Artifact,
    Quest,
    Coins,
};
constexpr size_t WorldItemSparkleCount = 6;
WorldItemSparkle worldItemSparkle(const InventoryItem &item, const ItemDefinition &definition, int value);
}
