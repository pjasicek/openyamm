#include "game/maps/DecorationModelSet.h"

#include "game/maps/DecorationModelPlacement.h"

#include "engine/AssetFileSystem.h"
#include "game/maps/MapAssetLoader.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <numbers>
#include <optional>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
std::string lowercase(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(),
        [](unsigned char value) { return char(std::tolower(value)); });
    return text;
}

// Triangles of each mesh node in asset space at rest, from the first coarser LOD when there is one: those of
// camera-facing (openyamm_billboard) materials, or all others.
std::vector<std::array<float, 3>> pickTriangles(const Engine::ModelAsset &asset, bool billboards)
{
    Engine::ModelPose rest;
    Engine::resetModelPose(asset, rest);
    Engine::evaluateModelHierarchy(asset, Engine::identityModelMatrix(), rest);
    std::vector<std::array<float, 3>> triangles;
    for (size_t node = 0; node < asset.nodes.size(); ++node)
    {
        const int32_t meshIndex = asset.nodes[node].meshIndex;
        if (meshIndex < 0 || size_t(meshIndex) >= asset.meshes.size() || node >= rest.globalMatrices.size())
        {
            continue;
        }
        const Engine::ModelMesh &base = asset.meshes[meshIndex];
        const Engine::ModelMesh &mesh = base.lodMeshes.empty() ? base : asset.meshes[base.lodMeshes.front()];
        const Engine::ModelMatrix &matrix = rest.globalMatrices[node];
        for (const Engine::ModelPrimitive &primitive : mesh.primitives)
        {
            const int material = primitive.materialIndices.front();
            const bool billboard = material >= 0 && size_t(material) < asset.materials.size()
                && asset.materials[size_t(material)].billboard;
            if (billboard != billboards)
            {
                continue;
            }
            for (const uint32_t vertex : primitive.indices)
            {
                const std::array<float, 3> &p = primitive.vertices[vertex].position;
                triangles.push_back({matrix[0] * p[0] + matrix[4] * p[1] + matrix[8] * p[2] + matrix[12],
                    matrix[1] * p[0] + matrix[5] * p[1] + matrix[9] * p[2] + matrix[13],
                    matrix[2] * p[0] + matrix[6] * p[1] + matrix[10] * p[2] + matrix[14]});
            }
        }
    }
    return triangles;
}

// A point (or direction) mapped by the inverse of a column-major affine matrix.
std::array<float, 3> transformInverse(const Engine::ModelMatrix &m, const std::array<float, 3> &v, bool point)
{
    const std::array<float, 3> d = point ? std::array<float, 3>{v[0] - m[12], v[1] - m[13], v[2] - m[14]} : v;
    const float a = m[0], b = m[4], c = m[8], e = m[1], f = m[5], g = m[9], h = m[2], i = m[6], j = m[10];
    const float det = a * (f * j - g * i) - b * (e * j - g * h) + c * (e * i - f * h);
    if (std::abs(det) < 1e-12f)
    {
        return {0.0f, 0.0f, 0.0f};
    }
    const float inv = 1.0f / det;
    return {((f * j - g * i) * d[0] - (b * j - c * i) * d[1] + (b * g - c * f) * d[2]) * inv,
        (-(e * j - g * h) * d[0] + (a * j - c * h) * d[1] - (a * g - c * e) * d[2]) * inv,
        ((e * i - f * h) * d[0] - (a * i - b * h) * d[1] + (a * f - b * e) * d[2]) * inv};
}

// Moller-Trumbore ray-triangle intersection (both faces).
bool intersectTriangle(const std::array<float, 3> &origin, const std::array<float, 3> &direction,
    const std::array<float, 3> &a, const std::array<float, 3> &b, const std::array<float, 3> &c, float &t)
{
    const std::array<float, 3> e1 = {b[0] - a[0], b[1] - a[1], b[2] - a[2]};
    const std::array<float, 3> e2 = {c[0] - a[0], c[1] - a[1], c[2] - a[2]};
    const std::array<float, 3> p = {direction[1] * e2[2] - direction[2] * e2[1],
        direction[2] * e2[0] - direction[0] * e2[2], direction[0] * e2[1] - direction[1] * e2[0]};
    const float det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2];
    if (std::abs(det) < 1e-12f)
    {
        return false;
    }
    const float inv = 1.0f / det;
    const std::array<float, 3> s = {origin[0] - a[0], origin[1] - a[1], origin[2] - a[2]};
    const float u = (s[0] * p[0] + s[1] * p[1] + s[2] * p[2]) * inv;
    if (u < 0.0f || u > 1.0f)
    {
        return false;
    }
    const std::array<float, 3> q = {s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
        s[0] * e1[1] - s[1] * e1[0]};
    const float v = (direction[0] * q[0] + direction[1] * q[1] + direction[2] * q[2]) * inv;
    if (v < 0.0f || u + v > 1.0f)
    {
        return false;
    }
    t = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv;
    return true;
}

// Stable per-placement variation from the map position, so a decoration looks the same every visit.
float placementRandom(int x, int y, uint32_t salt)
{
    uint32_t hash = uint32_t(x) * 0x9e3779b1u ^ uint32_t(y) * 0x85ebca77u ^ salt * 0xc2b2ae3du;
    hash ^= hash >> 15;
    hash *= 0x2c1b3c6du;
    hash ^= hash >> 12;
    hash *= 0x297a2d39u;
    hash ^= hash >> 15;
    return float(hash & 0xffffffu) / float(0x1000000u);
}

}

void DecorationModelSet::clear()
{
    m_bindings.clear();
    m_bindingBySprite.clear();
    m_groups.clear();
    m_billboardIndices.clear();
    m_restMatrices.clear();
    m_slots.clear();
    m_assets.clear();
    m_wallFinder = {};
    m_unmountedBillboards.clear();
    m_swingingGroups.clear();
}

bool DecorationModelSet::raycast(size_t billboardIndex, const std::array<float, 3> &origin,
    const std::array<float, 3> &direction, float &distance) const
{
    if (!drawsBillboard(billboardIndex))
    {
        return false;
    }
    const Slot &slot = m_slots[billboardIndex];
    const Engine::ModelStaticGroup &group = m_groups[slot.group];
    if (slot.index >= group.placements.size() || !group.placements[slot.index].visible)
    {
        return false;
    }
    const Engine::ModelMatrix &matrix = group.placements[slot.index].matrix;
    bool hit = false;
    float best = std::numeric_limits<float>::max();
    // Camera-facing cards (flames) face the ray's origin, as they face the camera when drawn. They turn outside the
    // rest bounds, so they skip the broad phase; models carry only a few of them.
    const std::vector<std::array<float, 3>> &cards = m_bindings[slot.group].billboardPickTriangles;
    for (size_t index = 0; index + 2 < cards.size(); index += 3)
    {
        float t = 0.0f;
        const std::array<float, 3> a = facingCardCorner(matrix, cards[index], origin);
        const std::array<float, 3> b = facingCardCorner(matrix, cards[index + 1], origin);
        const std::array<float, 3> c = facingCardCorner(matrix, cards[index + 2], origin);
        if (intersectTriangle(origin, direction, a, b, c, t) && t >= 0.0f && t < best)
        {
            best = t;
            hit = true;
        }
    }
    if (rigidHit(slot, origin, direction, best))
    {
        hit = true;
    }
    if (hit)
    {
        distance = best;
    }
    return hit;
}

bool DecorationModelSet::rigidHit(const Slot &slot, const std::array<float, 3> &origin,
    const std::array<float, 3> &direction, float &best) const
{
    const Engine::ModelStaticGroup &group = m_groups[size_t(slot.group)];
    // Broad phase against the placement's world bounds.
    const Engine::ModelBounds &bounds = group.bounds[slot.index];
    float enter = 0.0f;
    float leave = std::numeric_limits<float>::max();
    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (std::abs(direction[axis]) < 1e-9f)
        {
            if (origin[axis] < bounds.min[axis] || origin[axis] > bounds.max[axis])
            {
                return false;
            }
            continue;
        }
        float near = (bounds.min[axis] - origin[axis]) / direction[axis];
        float far = (bounds.max[axis] - origin[axis]) / direction[axis];
        if (near > far)
        {
            std::swap(near, far);
        }
        enter = std::max(enter, near);
        leave = std::min(leave, far);
        if (enter > leave)
        {
            return false;
        }
    }
    // The ray in asset space: the placement matrix is affine, so the ray parameter is the same in both spaces.
    const std::array<float, 3> localOrigin = transformInverse(group.placements[slot.index].matrix, origin, true);
    const std::array<float, 3> localDirection = transformInverse(group.placements[slot.index].matrix, direction, false);
    const std::vector<std::array<float, 3>> &triangles = m_bindings[size_t(slot.group)].pickTriangles;
    bool hit = false;
    for (size_t index = 0; index + 2 < triangles.size(); index += 3)
    {
        float t = 0.0f;
        if (intersectTriangle(localOrigin, localDirection, triangles[index], triangles[index + 1], triangles[index + 2],
                t) && t >= 0.0f && t < best)
        {
            best = t;
            hit = true;
        }
    }
    return hit;
}

Engine::ModelStaticPlacement DecorationModelSet::placementFor(const Binding &binding,
    const DecorationBillboard &billboard, const std::optional<DecorationWallContact> &wall) const
{
    const Engine::ModelBounds &bounds = binding.asset->staticBounds;
    const float scale = binding.height / (bounds.max[1] - bounds.min[1]) * heightJitter(binding, billboard);
    const float z = float(billboard.z) + binding.zOffset;
    Engine::ModelStaticPlacement placement;
    if (wall)
    {
        placement.matrix = wallMountedPlacement(*wall, bounds.min[2], z, scale);
        return placement;
    }
    const float yaw = (binding.randomYaw
        ? placementRandom(billboard.x, billboard.y, 2) * 2.0f * std::numbers::pi_v<float>
        : float(billboard.facing) * std::numbers::pi_v<float> / 180.0f) + binding.yawOffset;
    placement.matrix = Engine::composeModelTransform(Engine::gltfModelPlacement(
        {float(billboard.x), float(billboard.y), z}, yaw, scale));
    return placement;
}

float DecorationModelSet::heightJitter(const Binding &binding, const DecorationBillboard &billboard)
{
    return 1.0f + binding.heightJitter * (2.0f * placementRandom(billboard.x, billboard.y, 1) - 1.0f);
}

void DecorationModelSet::place(size_t billboardIndex, const DecorationBillboard &billboard, uint32_t binding)
{
    m_slots[billboardIndex].binding = int32_t(binding);
    // A wall-mounted model hangs on the nearest wall; without one in reach it stands free (its free_model), or is
    // reported and keeps the map facing.
    std::optional<DecorationWallContact> wall;
    if (m_bindings[binding].mountWall)
    {
        const Binding &mounted = m_bindings[binding];
        wall = m_wallFinder ? m_wallFinder(billboard, mounted.height * heightJitter(mounted, billboard))
            : std::nullopt;
        if (!wall && mounted.freeBinding >= 0)
        {
            binding = uint32_t(mounted.freeBinding);
        }
        else if (!wall && std::find(m_unmountedBillboards.begin(), m_unmountedBillboards.end(), billboardIndex)
            == m_unmountedBillboards.end())
        {
            m_unmountedBillboards.push_back(billboardIndex);
        }
    }
    Engine::ModelStaticGroup &group = m_groups[binding];
    group.placements.push_back(placementFor(m_bindings[binding], billboard, wall));
    m_restMatrices[binding].push_back(group.placements.back().matrix);
    group.bounds.push_back(group.placementBounds(group.placements.back()));
    m_billboardIndices[binding].push_back(billboardIndex);
    m_slots[billboardIndex].group = int32_t(binding);
    m_slots[billboardIndex].index = uint32_t(group.placements.size() - 1);
}

void DecorationModelSet::unplace(size_t billboardIndex)
{
    Slot &slot = m_slots[billboardIndex];
    if (slot.group < 0)
    {
        return;
    }
    // Swap-remove, keeping the renderer's per-placement LOD and crossfade state aligned.
    Engine::ModelStaticGroup &group = m_groups[size_t(slot.group)];
    std::vector<size_t> &indices = m_billboardIndices[size_t(slot.group)];
    const size_t last = group.placements.size() - 1;
    const auto swapRemove = [&](auto &values)
    {
        if (values.size() == group.placements.size())
        {
            values[slot.index] = values[last];
            values.pop_back();
        }
    };
    swapRemove(group.lodLevels);
    swapRemove(group.fades);
    swapRemove(group.bounds);
    swapRemove(m_restMatrices[size_t(slot.group)]);
    swapRemove(indices);
    group.placements[slot.index] = group.placements[last];
    group.placements.pop_back();
    if (slot.index < indices.size())
    {
        m_slots[indices[slot.index]].index = slot.index;
    }
    slot.group = -1;
    slot.binding = -1;
}

void DecorationModelSet::update(const std::vector<DecorationBillboard> &billboards,
    const std::function<uint16_t(size_t billboardIndex, bool &hidden)> &shownSprite)
{
    for (size_t index = 0; index < billboards.size() && index < m_slots.size(); ++index)
    {
        bool hidden = false;
        const uint16_t sprite = shownSprite(index, hidden);
        Slot &slot = m_slots[index];
        if (sprite != slot.sprite)
        {
            slot.sprite = sprite;
            const auto binding = m_bindingBySprite.find(sprite);
            const int32_t target = binding != m_bindingBySprite.end() ? int32_t(binding->second) : -1;
            if (target != slot.binding)
            {
                unplace(index);
                if (target >= 0)
                {
                    place(index, billboards[index], uint32_t(target));
                }
            }
        }
        if (slot.group >= 0)
        {
            m_groups[size_t(slot.group)].placements[slot.index].visible = !hidden;
        }
    }
}

void DecorationModelSet::animate(float timeSeconds)
{
    for (const uint32_t group : m_swingingGroups)
    {
        const Binding &binding = m_bindings[group];
        Engine::ModelStaticGroup &placements = m_groups[group];
        const Engine::ModelBounds &bounds = binding.asset->staticBounds;
        const std::array<float, 3> pivot = {(bounds.min[0] + bounds.max[0]) * 0.5f, bounds.max[1],
            (bounds.min[2] + bounds.max[2]) * 0.5f};
        for (size_t index = 0; index < placements.placements.size(); ++index)
        {
            const Engine::ModelMatrix &rest = m_restMatrices[group][index];
            // Each placement swings out of step with its neighbours (phase from its map position).
            const float phase = placementRandom(int(rest[12]), int(rest[13]), 3) * 2.0f * std::numbers::pi_v<float>;
            const float angle = binding.swingRadians
                * std::sin(2.0f * std::numbers::pi_v<float> * timeSeconds / binding.swingPeriod + phase);
            placements.placements[index].matrix = swungPlacement(rest, pivot, angle);
            placements.bounds[index] = placements.placementBounds(placements.placements[index]);
        }
    }
}

bool DecorationModelSet::load(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile, const DecorationBillboardSet &decorations, std::string &error, WallFinder wallFinder)
{
    clear();
    m_wallFinder = std::move(wallFinder);
    // Indoor bindings live apart: decorations.yml is a dependency of every baked outdoor map.
    const std::string lowerMap = lowercase(mapFile);
    const bool indoor = lowerMap.size() > 4 && lowerMap.ends_with(".blv");
    const std::string manifestPath =
        "worlds/" + worldId + "/models/" + (indoor ? "indoor_decorations.yml" : "decorations.yml");
    const std::optional<std::string> text = assets.readTextFile(manifestPath);
    if (!text)
    {
        return true;
    }
    std::unordered_map<std::string, uint32_t> bindingByName;
    try
    {
        const YAML::Node document = YAML::Load(*text);
        if (!document["decorations"].IsSequence())
        {
            error = "decoration model manifest requires a decorations sequence: " + manifestPath;
            return false;
        }
        for (const YAML::Node &entry : document["decorations"])
        {
            const std::string name = lowercase(entry["name"].as<std::string>());
            if (entry["maps"])
            {
                const std::vector<std::string> maps = entry["maps"].as<std::vector<std::string>>();
                if (std::none_of(maps.begin(), maps.end(),
                        [&](const std::string &map) { return lowercase(map) == lowercase(mapFile); }))
                {
                    continue;
                }
            }
            const DecorationEntry *pDecoration = decorations.decorationTable.findByInternalName(name);
            if (bindingByName.contains(name) || pDecoration == nullptr || pDecoration->spriteId == 0)
            {
                error = "unknown, sprite-less or duplicate decoration model binding: " + name;
                return false;
            }
            const Engine::ModelLoadResult loaded = m_assets.load(assets, entry["model"].as<std::string>());
            if (!loaded)
            {
                error = loaded.error;
                return false;
            }
            Binding binding;
            binding.asset = loaded.asset;
            binding.height = entry["height"].as<float>();
            binding.heightJitter = entry["height_jitter"].as<float>(0.0f);
            const std::string yaw = entry["yaw"].as<std::string>("random");
            if (yaw != "random" && yaw != "facing")
            {
                error = "decoration model yaw must be random or facing: " + name;
                return false;
            }
            binding.randomYaw = yaw == "random";
            binding.yawOffset = entry["yaw_offset"].as<float>(0.0f);
            binding.zOffset = entry["z_offset"].as<float>(0.0f);
            const std::string mount = entry["mount"].as<std::string>("ground");
            if (mount != "ground" && mount != "wall")
            {
                error = "decoration model mount must be ground or wall: " + name;
                return false;
            }
            binding.mountWall = mount == "wall";
            if (entry["swing"])
            {
                const std::vector<float> swing = entry["swing"].as<std::vector<float>>();
                if (swing.size() != 2 || !(swing[0] > 0.0f && swing[0] <= 45.0f)
                    || !(swing[1] >= 0.2f && swing[1] <= 60.0f))
                {
                    error = "decoration model swing needs [angle 0..45 degrees, period 0.2..60 seconds]: " + name;
                    return false;
                }
                binding.swingRadians = swing[0] * std::numbers::pi_v<float> / 180.0f;
                binding.swingPeriod = swing[1];
            }
            // Validated here; read by the animation regression (an animated sprite kept still on purpose).
            entry["still"].as<bool>(false);
            if (entry["lod_pixels"])
            {
                const std::vector<float> pixels = entry["lod_pixels"].as<std::vector<float>>();
                if (pixels.size() != 3 || !(pixels[0] > pixels[1] && pixels[1] > pixels[2] && pixels[2] > 0.0f))
                {
                    error = "decoration model lod_pixels needs three decreasing sizes: " + name;
                    return false;
                }
                std::copy(pixels.begin(), pixels.end(), binding.lodPixels.begin());
            }
            const Engine::ModelBounds &bounds = binding.asset->staticBounds;
            if (!bounds.valid || bounds.max[1] - bounds.min[1] <= 0.0f || !std::isfinite(binding.height)
                || binding.height <= 0.0f || binding.heightJitter < 0.0f || binding.heightJitter >= 1.0f
                || !std::isfinite(binding.yawOffset) || !std::isfinite(binding.zOffset))
            {
                error = "invalid decoration model placement: " + name;
                return false;
            }
            if (!binding.asset->skins.empty() || !binding.asset->clips.empty())
            {
                error = "decoration models must be static (no skin or animation): " + name;
                return false;
            }
            if (m_bindingBySprite.contains(pDecoration->spriteId))
            {
                error = "decoration model bindings share a sprite: " + name;
                return false;
            }
            binding.pickTriangles = pickTriangles(*binding.asset, false);
            binding.billboardPickTriangles = pickTriangles(*binding.asset, true);
            std::optional<Binding> freeStanding;
            if (entry["free_model"])
            {
                const Engine::ModelLoadResult free = m_assets.load(assets, entry["free_model"].as<std::string>());
                if (!binding.mountWall || !free || !free.asset->skins.empty() || !free.asset->clips.empty()
                    || !free.asset->staticBounds.valid
                    || free.asset->staticBounds.max[1] - free.asset->staticBounds.min[1] <= 0.0f)
                {
                    error = !binding.mountWall ? "decoration model free_model needs mount: wall: " + name
                        : !free ? free.error : "invalid or animated decoration free_model: " + name;
                    return false;
                }
                freeStanding = binding;
                freeStanding->asset = free.asset;
                freeStanding->mountWall = false;
                freeStanding->pickTriangles = pickTriangles(*free.asset, false);
                freeStanding->billboardPickTriangles = pickTriangles(*free.asset, true);
            }
            const uint32_t index = uint32_t(m_bindings.size());
            bindingByName.emplace(name, index);
            m_bindingBySprite.emplace(pDecoration->spriteId, index);
            if (freeStanding)
            {
                binding.freeBinding = int32_t(index + 1);
            }
            m_bindings.push_back(std::move(binding));
            if (freeStanding)
            {
                m_bindings.push_back(std::move(*freeStanding));
            }
            // Binding i draws into group i (a free-standing binding after the binding it serves).
            for (size_t added = index; added < m_bindings.size(); ++added)
            {
                const Binding &drawn = m_bindings[added];
                m_groups.push_back({drawn.asset, 0, drawn.lodPixels, {}, {}, {}, {}});
                m_billboardIndices.emplace_back();
                m_restMatrices.emplace_back();
                if (drawn.swingPeriod > 0.0f)
                {
                    m_swingingGroups.push_back(uint32_t(added));
                }
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = manifestPath + ": " + exception.what();
        return false;
    }

    // Initial placements from each decoration's own sprite; update() follows event sprite switches.
    m_slots.assign(decorations.billboards.size(), {});
    for (size_t index = 0; index < decorations.billboards.size(); ++index)
    {
        const DecorationBillboard &billboard = decorations.billboards[index];
        m_slots[index].sprite = billboard.spriteId;
        const auto binding = m_bindingBySprite.find(billboard.spriteId);
        if (binding != m_bindingBySprite.end())
        {
            place(index, billboard, binding->second);
        }
    }
    return true;
}
}
