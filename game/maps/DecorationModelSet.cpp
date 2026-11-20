#include "game/maps/DecorationModelSet.h"

#include "game/maps/DecorationModelManifest.h"
#include "game/maps/DecorationModelPlacement.h"

#include "engine/AssetFileSystem.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/maps/MapAssetLoader.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <numbers>
#include <optional>
#include <unordered_map>
#include <unordered_set>

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
std::vector<std::array<float, 3>> pickTriangles(const Engine::ModelAsset &asset, bool billboards,
    std::vector<std::array<float, 3>> *pCardPivots = nullptr)
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
            const auto toAsset = [&matrix](const std::array<float, 3> &p)
            {
                return std::array<float, 3>{matrix[0] * p[0] + matrix[4] * p[1] + matrix[8] * p[2] + matrix[12],
                    matrix[1] * p[0] + matrix[5] * p[1] + matrix[9] * p[2] + matrix[13],
                    matrix[2] * p[0] + matrix[6] * p[1] + matrix[10] * p[2] + matrix[14]};
            };
            // A card billboard turns about its primitive's centre (ModelRenderer: the bounds' centre), others about
            // the model origin.
            std::array<float, 3> pivot = {};
            if (billboard && asset.materials[size_t(material)].billboardCard && !primitive.vertices.empty())
            {
                std::array<float, 3> low = primitive.vertices.front().position;
                std::array<float, 3> high = low;
                for (const Engine::ModelVertex &vertex : primitive.vertices)
                {
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        low[axis] = std::min(low[axis], vertex.position[axis]);
                        high[axis] = std::max(high[axis], vertex.position[axis]);
                    }
                }
                pivot = toAsset({(low[0] + high[0]) * 0.5f, (low[1] + high[1]) * 0.5f, (low[2] + high[2]) * 0.5f});
            }
            for (const uint32_t vertex : primitive.indices)
            {
                triangles.push_back(toAsset(primitive.vertices[vertex].position));
                if (pCardPivots != nullptr)
                {
                    pCardPivots->push_back(pivot);
                }
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

// A rigid placement matrix (uniform scale) as a model transform.
Engine::ModelTransform modelTransformOf(const Engine::ModelMatrix &m)
{
    Engine::ModelTransform transform;
    const float scale = std::sqrt(m[0] * m[0] + m[1] * m[1] + m[2] * m[2]);
    transform.translation = {m[12], m[13], m[14]};
    transform.scale = {scale, scale, scale};
    if (scale <= 0.0f)
    {
        return transform;
    }
    const float r00 = m[0] / scale, r10 = m[1] / scale, r20 = m[2] / scale;
    const float r01 = m[4] / scale, r11 = m[5] / scale, r21 = m[6] / scale;
    const float r02 = m[8] / scale, r12 = m[9] / scale, r22 = m[10] / scale;
    const float trace = r00 + r11 + r22;
    std::array<float, 4> q = {};
    if (trace > 0.0f)
    {
        const float t = std::sqrt(trace + 1.0f) * 2.0f;
        q = {(r21 - r12) / t, (r02 - r20) / t, (r10 - r01) / t, 0.25f * t};
    }
    else if (r00 > r11 && r00 > r22)
    {
        const float t = std::sqrt(1.0f + r00 - r11 - r22) * 2.0f;
        q = {0.25f * t, (r01 + r10) / t, (r02 + r20) / t, (r21 - r12) / t};
    }
    else if (r11 > r22)
    {
        const float t = std::sqrt(1.0f + r11 - r00 - r22) * 2.0f;
        q = {(r01 + r10) / t, 0.25f * t, (r12 + r21) / t, (r02 - r20) / t};
    }
    else
    {
        const float t = std::sqrt(1.0f + r22 - r00 - r11) * 2.0f;
        q = {(r02 + r20) / t, (r12 + r21) / t, 0.25f * t, (r10 - r01) / t};
    }
    transform.rotation = q;
    return transform;
}

}

bool DecorationModelSet::rigidMovingNode(Binding &binding, std::string &error)
{
    // One rigid mesh node (its LODs on it), moved by the clips.
    std::optional<uint32_t> meshNode;
    for (size_t node = 0; node < binding.asset->nodes.size(); ++node)
    {
        if (binding.asset->nodes[node].meshIndex >= 0)
        {
            meshNode = meshNode ? std::optional<uint32_t>(UINT32_MAX) : std::optional<uint32_t>(uint32_t(node));
        }
    }
    if (!meshNode || *meshNode == UINT32_MAX || !binding.asset->skins.empty() || !binding.asset->staticBounds.valid)
    {
        error = "needs one rigid mesh node";
        return false;
    }
    Engine::ModelPose rest;
    Engine::resetModelPose(*binding.asset, rest);
    Engine::evaluateModelHierarchy(*binding.asset, Engine::identityModelMatrix(), rest);
    const Engine::ModelMatrix &matrix = rest.globalMatrices[*meshNode];
    if (std::abs(Engine::determinant3x3(matrix)) < 1e-12f)
    {
        error = "its mesh node is degenerate at rest";
        return false;
    }
    // The rest matrix is affine: its inverse from the inverse of its upper 3x3 and the moved origin.
    Engine::ModelMatrix inverse = Engine::identityModelMatrix();
    for (size_t column = 0; column < 3; ++column)
    {
        std::array<float, 3> axis = {};
        axis[column] = 1.0f;
        const std::array<float, 3> mapped = transformInverse(matrix, axis, false);
        for (size_t row = 0; row < 3; ++row)
        {
            inverse[column * 4 + row] = mapped[row];
        }
    }
    const std::array<float, 3> origin = transformInverse(matrix, {0.0f, 0.0f, 0.0f}, true);
    for (size_t row = 0; row < 3; ++row)
    {
        inverse[12 + row] = origin[row];
    }
    binding.partNode = *meshNode;
    binding.partRestInverse = inverse;
    return true;
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
    m_partGroups.clear();
    m_selfAnimatedGroups.clear();
    m_animatedGroups.clear();
    m_useGroups.clear();
    m_turningBillboards.clear();
    m_settled = false;
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
    if (slot.index >= group.placements.size() || slot.hidden)
    {
        return false;
    }
    const Engine::ModelMatrix &matrix = group.placements[slot.index].matrix;
    bool hit = false;
    float best = std::numeric_limits<float>::max();
    // Camera-facing cards (flames) face the ray's origin, as they face the camera when drawn. They turn outside the
    // rest bounds, so they skip the broad phase; models carry only a few of them.
    const std::vector<std::array<float, 3>> &cards = m_bindings[slot.group].billboardPickTriangles;
    const std::vector<std::array<float, 3>> &pivots = m_bindings[slot.group].billboardPickPivots;
    for (size_t index = 0; index + 2 < cards.size(); index += 3)
    {
        float t = 0.0f;
        const std::array<float, 3> a = facingCardCorner(matrix, cards[index], origin, pivots[index]);
        const std::array<float, 3> b = facingCardCorner(matrix, cards[index + 1], origin, pivots[index + 1]);
        const std::array<float, 3> c = facingCardCorner(matrix, cards[index + 2], origin, pivots[index + 2]);
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

std::optional<DecorationPortraitModel> DecorationModelSet::portraitModel(
    const std::vector<DecorationBillboard> &billboards, uint32_t spriteOverrideKey) const
{
    std::optional<DecorationPortraitModel> found;
    for (size_t index = 0; index < billboards.size() && index < m_slots.size(); ++index)
    {
        if (billboards[index].spriteOverrideKey() != spriteOverrideKey)
        {
            continue;
        }
        const Slot &slot = m_slots[index];
        if (found || slot.group < 0 || slot.binding < 0 || size_t(slot.binding) >= m_bindings.size())
        {
            return std::nullopt;
        }
        const Binding &binding = m_bindings[size_t(slot.binding)];
        const Engine::ModelBounds &bounds = binding.asset->staticBounds;
        const float extent = bounds.max[1] - bounds.min[1];
        // A decoration placed at facing 0 shows its front a quarter turn from +X (a posed figure at facing 270 faces
        // +X in the world): a quarter turn back turns it to the portrait's camera.
        found = DecorationPortraitModel{binding.asset, binding.materialVariant,
            binding.yawOffset - 0.5f * std::numbers::pi_v<float>, extent > 0.0f ? binding.height / extent : 1.0f};
    }
    return found;
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
    placePart(billboardIndex);
}

std::optional<size_t> DecorationModelSet::removePlacement(size_t group, uint32_t index)
{
    // Swap-remove, keeping the renderer's per-placement LOD and crossfade state aligned.
    Engine::ModelStaticGroup &placements = m_groups[group];
    std::vector<size_t> &indices = m_billboardIndices[group];
    const size_t last = placements.placements.size() - 1;
    const auto swapRemove = [&](auto &values)
    {
        if (values.size() == placements.placements.size())
        {
            values[index] = values[last];
            values.pop_back();
        }
    };
    swapRemove(placements.lodLevels);
    swapRemove(placements.fades);
    swapRemove(placements.bounds);
    swapRemove(m_restMatrices[group]);
    swapRemove(indices);
    placements.placements[index] = placements.placements[last];
    placements.placements.pop_back();
    return index < indices.size() ? std::optional<size_t>(indices[index]) : std::nullopt;
}

void DecorationModelSet::unplace(size_t billboardIndex)
{
    unplaceOverlay(billboardIndex);
    unplacePart(billboardIndex);
    Slot &slot = m_slots[billboardIndex];
    if (slot.group < 0)
    {
        return;
    }
    if (const std::optional<size_t> moved = removePlacement(size_t(slot.group), slot.index))
    {
        m_slots[*moved].index = slot.index;
    }
    slot.group = -1;
    slot.binding = -1;
}

void DecorationModelSet::placeOverlay(size_t billboardIndex)
{
    Slot &slot = m_slots[billboardIndex];
    if (slot.group < 0 || slot.binding < 0 || slot.state < 0)
    {
        return;
    }
    const std::vector<int32_t> &overlays = m_bindings[size_t(slot.binding)].stateOverlays;
    if (size_t(slot.state) >= overlays.size() || overlays[size_t(slot.state)] < 0)
    {
        return;
    }
    const size_t overlay = size_t(overlays[size_t(slot.state)]);
    Engine::ModelStaticGroup &group = m_groups[overlay];
    Engine::ModelStaticPlacement placement;
    placement.matrix = m_groups[size_t(slot.group)].placements[slot.index].matrix;
    group.placements.push_back(placement);
    m_restMatrices[overlay].push_back(placement.matrix);
    group.bounds.push_back(group.placementBounds(placement));
    m_billboardIndices[overlay].push_back(billboardIndex);
    slot.overlayGroup = int32_t(overlay);
    slot.overlayIndex = uint32_t(group.placements.size() - 1);
}

void DecorationModelSet::unplaceOverlay(size_t billboardIndex)
{
    Slot &slot = m_slots[billboardIndex];
    if (slot.overlayGroup < 0)
    {
        return;
    }
    if (const std::optional<size_t> moved = removePlacement(size_t(slot.overlayGroup), slot.overlayIndex))
    {
        m_slots[*moved].overlayIndex = slot.overlayIndex;
    }
    slot.overlayGroup = -1;
}

void DecorationModelSet::placePart(size_t billboardIndex)
{
    Slot &slot = m_slots[billboardIndex];
    if (slot.group < 0)
    {
        return;
    }
    for (const int32_t part : m_bindings[size_t(slot.group)].parts)
    {
        Engine::ModelStaticGroup &group = m_groups[size_t(part)];
        Engine::ModelStaticPlacement placement;
        placement.matrix = m_groups[size_t(slot.group)].placements[slot.index].matrix;
        group.placements.push_back(placement);
        m_restMatrices[size_t(part)].push_back(placement.matrix);
        group.bounds.push_back(group.placementBounds(placement));
        m_billboardIndices[size_t(part)].push_back(billboardIndex);
        slot.parts.emplace_back(part, uint32_t(group.placements.size() - 1));
    }
}

void DecorationModelSet::unplacePart(size_t billboardIndex)
{
    std::vector<std::pair<int32_t, uint32_t>> parts = std::move(m_slots[billboardIndex].parts);
    m_slots[billboardIndex].parts.clear();
    for (const auto &[group, index] : parts)
    {
        if (const std::optional<size_t> moved = removePlacement(size_t(group), index))
        {
            for (auto &entry : m_slots[*moved].parts)
            {
                if (entry.first == group)
                {
                    entry.second = index;
                }
            }
        }
    }
}

void DecorationModelSet::noteUses(const std::vector<DecorationBillboard> &billboards, const UseCount &uses,
    float timeSeconds)
{
    for (const uint32_t group : m_useGroups)
    {
        const Binding &binding = m_bindings[group];
        for (const size_t billboardIndex : m_billboardIndices[group])
        {
            Slot &slot = m_slots[billboardIndex];
            const uint32_t count = billboardIndex < billboards.size()
                ? uses(billboards[billboardIndex].spriteOverrideKey()) : 0;
            if (count == slot.uses)
            {
                continue;
            }
            slot.useClip = (slot.useClip + int32_t(count - slot.uses)) % int32_t(binding.useClips.size());
            slot.uses = count;
            slot.useStart = timeSeconds;
        }
    }
}

bool DecorationModelSet::resolveClip(const Binding &binding, const Engine::ModelAsset &asset,
    const DecorationBillboard *pBillboard, const Slot *pSlot, const PartClip &clip, float timeSeconds,
    uint32_t &clipIndex, float &seconds) const
{
    std::string clipName;
    bool loop = false;
    std::optional<uint32_t> found;
    if (pBillboard != nullptr && clip && clip(pBillboard->spriteOverrideKey(), clipName, seconds, loop))
    {
        found = asset.findClip(clipName);
    }
    if (!found && pSlot != nullptr && pSlot->useClip >= 0 && size_t(pSlot->useClip) < binding.useClips.size())
    {
        found = asset.findClip(binding.useClips[size_t(pSlot->useClip)]);
        loop = false;
        seconds = timeSeconds - pSlot->useStart;
    }
    if (!found && !binding.idleClip.empty())
    {
        found = asset.findClip(binding.idleClip);
        loop = true;
        // Each placement out of step with its neighbours (phase from its map position).
        seconds = timeSeconds + (pBillboard != nullptr
            ? placementRandom(pBillboard->x, pBillboard->y, 4) * 60.0f : 0.0f);
    }
    if (!found)
    {
        return false;
    }
    clipIndex = *found;
    const float duration = asset.clips[clipIndex].durationSeconds;
    seconds = duration <= 0.0f ? 0.0f
        : loop ? std::fmod(std::max(0.0f, seconds), duration) : std::clamp(seconds, 0.0f, duration);
    return true;
}

Engine::ModelMatrix DecorationModelSet::clipDelta(const Binding &moving, uint32_t clipIndex, float seconds)
{
    // The node's pose relative to its rest: the static draw already places the node at rest.
    Engine::resetModelPose(*moving.asset, m_partPose);
    Engine::evaluateModelClip(*moving.asset, clipIndex, seconds, m_partPose);
    Engine::evaluateModelHierarchy(*moving.asset, Engine::identityModelMatrix(), m_partPose);
    if (moving.partNode >= m_partPose.globalMatrices.size())
    {
        return Engine::identityModelMatrix();
    }
    return Engine::multiplyModelMatrices(m_partPose.globalMatrices[moving.partNode], moving.partRestInverse);
}

void DecorationModelSet::poseParts(const std::vector<DecorationBillboard> &billboards, const PartClip &clip,
    float timeSeconds)
{
    // Whole models first (from their rest: they are still bindings), then the parts that follow their decoration.
    for (const uint32_t group : m_selfAnimatedGroups)
    {
        const Binding &binding = m_bindings[group];
        Engine::ModelStaticGroup &placements = m_groups[group];
        for (size_t index = 0; index < placements.placements.size(); ++index)
        {
            const size_t billboardIndex = m_billboardIndices[group][index];
            Engine::ModelStaticPlacement &placement = placements.placements[index];
            placement.matrix = m_restMatrices[group][index];
            uint32_t clipIndex = 0;
            float seconds = 0.0f;
            if (resolveClip(binding, *binding.asset, billboardIndex < billboards.size() ? &billboards[billboardIndex]
                    : nullptr, &m_slots[billboardIndex], clip, timeSeconds, clipIndex, seconds))
            {
                placement.matrix = Engine::multiplyModelMatrices(placement.matrix,
                    clipDelta(binding, clipIndex, seconds));
            }
            placements.bounds[index] = placements.placementBounds(placement);
        }
    }
    for (const uint32_t partGroup : m_partGroups)
    {
        const Binding &part = m_bindings[partGroup];
        Engine::ModelStaticGroup &placements = m_groups[partGroup];
        const std::vector<size_t> &billboardIndices = m_billboardIndices[partGroup];
        for (size_t index = 0; index < placements.placements.size(); ++index)
        {
            const size_t billboardIndex = billboardIndices[index];
            const Slot &slot = m_slots[billboardIndex];
            Engine::ModelStaticPlacement &placement = placements.placements[index];
            // A part moves in its decoration's asset space: from the decoration's rest when the model itself moves.
            placement.matrix = m_bindings[size_t(slot.group)].selfAnimated
                ? m_restMatrices[size_t(slot.group)][slot.index]
                : m_groups[size_t(slot.group)].placements[slot.index].matrix;
            uint32_t clipIndex = 0;
            float seconds = 0.0f;
            if (resolveClip(m_bindings[size_t(slot.group)], *part.asset, billboardIndex < billboards.size()
                    ? &billboards[billboardIndex] : nullptr, &slot, clip, timeSeconds, clipIndex, seconds))
            {
                placement.matrix = Engine::multiplyModelMatrices(placement.matrix,
                    clipDelta(part, clipIndex, seconds));
            }
            placements.bounds[index] = placements.placementBounds(placement);
        }
    }
}

void DecorationModelSet::poseInstances(const std::vector<DecorationBillboard> &billboards, const PartClip &clip,
    float timeSeconds, Engine::ModelInstanceSystem &models)
{
    for (const uint32_t group : m_animatedGroups)
    {
        const Binding &binding = m_bindings[group];
        Engine::ModelStaticGroup &placements = m_groups[group];
        for (size_t index = 0; index < placements.placements.size(); ++index)
        {
            const size_t billboardIndex = m_billboardIndices[group][index];
            Slot &slot = m_slots[billboardIndex];
            Engine::ModelStaticPlacement &placement = placements.placements[index];
            // The static model stays for picking (raycast follows the slot's hidden state), never drawn.
            placement.visible = false;
            uint32_t clipIndex = 0;
            float seconds = 0.0f;
            const bool posed = resolveClip(binding, *binding.animatedAsset, billboardIndex < billboards.size()
                    ? &billboards[billboardIndex] : nullptr, &slot, clip, timeSeconds, clipIndex, seconds);
            const std::string clipName = posed ? binding.animatedAsset->clips[clipIndex].name : std::string();
            // Back to rest: a fresh instance shows it.
            if (slot.instance && !posed && !slot.instanceClip.empty())
            {
                models.destroy(*slot.instance);
                slot.instance.reset();
            }
            if (!slot.instance || !models.contains(*slot.instance))
            {
                slot.instance = models.create(binding.animatedAsset, {});
                slot.instanceClip.clear();
                slot.instanceSeconds = -1.0f;
            }
            const Engine::ModelTransform transform = modelTransformOf(placement.matrix);
            const Engine::ModelTransform *pCurrent = models.rootTransform(*slot.instance);
            const bool unchanged = pCurrent != nullptr && *pCurrent == transform && clipName == slot.instanceClip
                && seconds == slot.instanceSeconds;
            if (posed && !unchanged)
            {
                models.sample(*slot.instance, clipIndex, seconds, transform);
            }
            else if (!posed)
            {
                models.setTransform(*slot.instance, transform);
            }
            slot.instanceClip = clipName;
            slot.instanceSeconds = posed ? seconds : -1.0f;
            models.setVisible(*slot.instance, !slot.hidden);
        }
    }
}

void DecorationModelSet::update(const std::vector<DecorationBillboard> &billboards, const ShownSprite &shownSprite)
{
    for (size_t index = 0; index < billboards.size() && index < m_slots.size(); ++index)
    {
        bool hidden = false;
        int state = -1;
        const uint16_t sprite = shownSprite(index, hidden, state);
        Slot &slot = m_slots[index];
        if (sprite != slot.sprite)
        {
            slot.sprite = sprite;
            const auto binding = m_bindingBySprite.find(sprite);
            const int32_t target = binding != m_bindingBySprite.end() ? int32_t(binding->second) : -1;
            if (target != slot.binding)
            {
                const bool wasPlaced = slot.binding >= 0;
                unplace(index);
                slot.turning = false;
                if (target >= 0)
                {
                    place(index, billboards[index], uint32_t(target));
                    placeOverlay(index);
                    if (wasPlaced && m_settled && m_bindings[size_t(target)].turnSeconds > 0.0f)
                    {
                        slot.turning = true;
                        slot.turnStart = -1.0f;
                        m_turningBillboards.push_back(index);
                    }
                }
            }
        }
        if (state != slot.state)
        {
            slot.state = state;
            unplaceOverlay(index);
            placeOverlay(index);
        }
        if (slot.group >= 0)
        {
            m_groups[size_t(slot.group)].placements[slot.index].visible = !hidden;
        }
        if (slot.overlayGroup >= 0)
        {
            m_groups[size_t(slot.overlayGroup)].placements[slot.overlayIndex].visible = !hidden;
        }
        for (const auto &[group, partIndex] : slot.parts)
        {
            m_groups[size_t(group)].placements[partIndex].visible = !hidden;
        }
        slot.hidden = hidden;
    }
    m_settled = true;
}

void DecorationModelSet::pose(size_t billboardIndex, float yawRadians, float back, const std::array<float, 3> &offset)
{
    if (billboardIndex >= m_slots.size() || m_slots[billboardIndex].group < 0 || m_slots[billboardIndex].turning)
    {
        return;
    }

    const Slot &slot = m_slots[billboardIndex];
    const auto posed = [yawRadians, back, &offset](const Engine::ModelMatrix &rest)
    {
        Engine::ModelMatrix matrix = rest;
        const float cosine = std::cos(yawRadians);
        const float sine = std::sin(yawRadians);
        for (size_t column = 0; column < 3; ++column)
        {
            const float x = rest[column * 4];
            const float y = rest[column * 4 + 1];
            matrix[column * 4] = cosine * x - sine * y;
            matrix[column * 4 + 1] = sine * x + cosine * y;
        }
        const float length = std::sqrt(matrix[8] * matrix[8] + matrix[9] * matrix[9] + matrix[10] * matrix[10]);
        if (length > 0.0f)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                matrix[12 + axis] -= matrix[8 + axis] / length * back;
            }
        }
        for (size_t axis = 0; axis < 3; ++axis)
        {
            matrix[12 + axis] += offset[axis];
        }
        return matrix;
    };
    for (const auto &[group, index] :
        {std::pair{slot.group, slot.index}, std::pair{slot.overlayGroup, slot.overlayIndex}})
    {
        if (group >= 0)
        {
            Engine::ModelStaticGroup &placements = m_groups[size_t(group)];
            placements.placements[index].matrix = posed(m_restMatrices[size_t(group)][index]);
            placements.bounds[index] = placements.placementBounds(placements.placements[index]);
        }
    }
}

void DecorationModelSet::poseAimed(const std::vector<DecorationBillboard> &billboards, const Aimed &aimed)
{
    for (size_t index = 0; index < billboards.size() && index < m_slots.size(); ++index)
    {
        float yawRadians = 0.0f;
        float back = 0.0f;
        std::array<float, 3> offset = {};
        if (aimed(billboards[index].spriteOverrideKey(), yawRadians, back, offset))
        {
            pose(index, yawRadians, back, offset);
        }
    }
}

void DecorationModelSet::animate(float timeSeconds)
{
    for (size_t entry = 0; entry < m_turningBillboards.size();)
    {
        Slot &slot = m_slots[m_turningBillboards[entry]];
        if (!slot.turning || slot.group < 0)
        {
            slot.turning = false;
            m_turningBillboards[entry] = m_turningBillboards.back();
            m_turningBillboards.pop_back();
            continue;
        }
        if (slot.turnStart < 0.0f)
        {
            slot.turnStart = timeSeconds;
        }
        const Binding &binding = m_bindings[size_t(slot.binding)];
        Engine::ModelStaticGroup &placements = m_groups[size_t(slot.group)];
        const Engine::ModelBounds &bounds = binding.asset->staticBounds;
        const std::array<float, 3> pivot = {(bounds.min[0] + bounds.max[0]) * 0.5f,
            (bounds.min[1] + bounds.max[1]) * 0.5f, 0.0f};
        const float angle = turnRemaining(binding.turnRadians, binding.turnSeconds, timeSeconds - slot.turnStart);
        const Engine::ModelMatrix &rest = m_restMatrices[size_t(slot.group)][slot.index];
        placements.placements[slot.index].matrix = angle == 0.0f ? rest : turnedPlacement(rest, pivot, angle);
        placements.bounds[slot.index] = placements.placementBounds(placements.placements[slot.index]);
        if (angle == 0.0f)
        {
            slot.turning = false;
        }
        ++entry;
    }
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

bool DecorationModelSet::loadStateOverlays(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::unordered_map<std::string, uint32_t> &bindingByName, std::string &error)
{
    // Apart from decorations.yml, a dependency of every baked outdoor map: overlays cast no baked shadow.
    std::vector<YAML::Node> entries;
    if (!decorationOverlayEntries(assets, worldId, entries, error))
    {
        return false;
    }
    try
    {
        for (const YAML::Node &entry : entries)
        {
            const std::string name = lowercase(entry["name"].as<std::string>());
            const auto bound = bindingByName.find(name);
            if (bound == bindingByName.end())
            {
                // The decoration has no model on this map.
                continue;
            }
            const uint32_t served = bound->second;
            if (!entry["states"].IsSequence() || m_bindings[served].swingPeriod > 0.0f
                || !m_bindings[served].stateOverlays.empty())
            {
                error = "decoration overlay needs a states sequence, a still binding and one entry: " + name;
                return false;
            }
            // One overlay binding (and group) per state that shows one; null states show none.
            std::vector<int32_t> stateOverlays;
            for (const YAML::Node &state : entry["states"])
            {
                if (state.IsNull())
                {
                    stateOverlays.push_back(-1);
                    continue;
                }
                const Engine::ModelLoadResult loaded = m_assets.load(assets, state.as<std::string>());
                if (!loaded || !loaded.asset->skins.empty() || !loaded.asset->clips.empty()
                    || !loaded.asset->staticBounds.valid)
                {
                    error = !loaded ? loaded.error : "invalid or animated decoration overlay: " + name;
                    return false;
                }
                stateOverlays.push_back(int32_t(m_bindings.size()));
                Binding overlay;
                overlay.asset = loaded.asset;
                overlay.lodPixels = m_bindings[served].lodPixels;
                overlay.overlay = true;
                m_bindings.push_back(std::move(overlay));
                m_groups.push_back({loaded.asset, 0, m_bindings.back().lodPixels, {}, {}, {}, {}});
                m_billboardIndices.emplace_back();
                m_restMatrices.emplace_back();
            }
            m_bindings[served].stateOverlays = std::move(stateOverlays);
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = "decoration overlay manifest: " + std::string(exception.what());
        return false;
    }
    return true;
}

bool DecorationModelSet::loadParts(const Engine::AssetFileSystem &assets, const YAML::Node &entry,
    const std::string &name, uint32_t served, std::string &error)
{
    if (!entry["parts"].IsSequence() || m_bindings[served].swingPeriod > 0.0f || m_bindings[served].turnSeconds > 0.0f
        || m_bindings[served].mountWall)
    {
        error = "decoration model parts need a list and a still ground binding: " + name;
        return false;
    }
    for (const YAML::Node &path : entry["parts"])
    {
        const Engine::ModelLoadResult loaded = m_assets.load(assets, path.as<std::string>());
        if (!loaded)
        {
            error = loaded.error;
            return false;
        }
        Binding part;
        part.asset = loaded.asset;
        part.lodPixels = m_bindings[served].lodPixels;
        part.materialVariant = m_bindings[served].materialVariant;
        if (!rigidMovingNode(part, error))
        {
            error = "decoration model part " + path.as<std::string>() + ": " + error + ": " + name;
            return false;
        }
        m_bindings[served].parts.push_back(int32_t(m_bindings.size()));
        m_bindings.push_back(std::move(part));
        const Binding &added = m_bindings.back();
        m_groups.push_back({added.asset, added.materialVariant, added.lodPixels, {}, {}, {}, {}});
        m_billboardIndices.emplace_back();
        m_restMatrices.emplace_back();
        m_partGroups.push_back(uint32_t(m_bindings.size() - 1));
    }
    return true;
}

bool DecorationModelSet::load(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile, const DecorationBillboardSet &decorations, std::string &error, WallFinder wallFinder)
{
    clear();
    m_wallFinder = std::move(wallFinder);
    std::vector<YAML::Node> entries;
    if (!decorationModelEntries(assets, worldId, mapFile, entries, error))
    {
        return false;
    }
    // Only the decorations this map can show load their models: its placements, their lit/unlit counterparts and
    // its events' SetSprite targets (the engine manifests bind every world's decorations).
    std::unordered_set<std::string> shown = mapEventSpriteNames(assets, worldId, mapFile);
    for (const DecorationBillboard &billboard : decorations.billboards)
    {
        const DecorationEntry *pPlaced = decorations.decorationTable.get(billboard.decorationId);
        if (pPlaced == nullptr)
        {
            continue;
        }
        shown.insert(pPlaced->internalName);
        if (const DecorationEntry *pCounterpart = toggleableDecorationCounterpart(decorations.decorationTable, *pPlaced))
        {
            shown.insert(pCounterpart->internalName);
        }
    }
    std::unordered_map<std::string, uint32_t> bindingByName;
    try
    {
        for (const YAML::Node &entry : entries)
        {
            const std::string name = lowercase(entry["name"].as<std::string>());
            if (!shown.contains(name))
            {
                continue;
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
            if (entry["turn_in"])
            {
                const std::vector<float> turn = entry["turn_in"].as<std::vector<float>>();
                if (turn.size() != 2 || !(std::abs(turn[0]) > 0.0f && std::abs(turn[0]) <= 720.0f)
                    || !(turn[1] > 0.0f && turn[1] <= 10.0f))
                {
                    error = "decoration model turn_in needs [angle -720..720 degrees, 0..10 seconds]: " + name;
                    return false;
                }
                binding.turnRadians = turn[0] * std::numbers::pi_v<float> / 180.0f;
                binding.turnSeconds = turn[1];
            }
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
            if (entry["variant"])
            {
                const std::string variant = entry["variant"].as<std::string>();
                const std::vector<std::string> &variants = binding.asset->materialVariants;
                const auto found = std::find(variants.begin(), variants.end(), variant);
                if (found == variants.end())
                {
                    error = "decoration model variant " + variant + " is not one of its model's: " + name;
                    return false;
                }
                binding.materialVariant = uint32_t(found - variants.begin()) + 1;
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
            const bool still = binding.swingPeriod <= 0.0f && binding.turnSeconds <= 0.0f && !binding.mountWall;
            if (!binding.asset->skins.empty())
            {
                error = "decoration models must be rigid (no skin; a skinned copy is its animated model): " + name;
                return false;
            }
            // A model with clips moves as a whole (its one rigid mesh node).
            if (!binding.asset->clips.empty())
            {
                if (!still || !rigidMovingNode(binding, error))
                {
                    error = "decoration model with clips: " + (still ? error : "needs a still ground binding") + ": "
                        + name;
                    return false;
                }
                binding.selfAnimated = true;
            }
            binding.idleClip = entry["idle"].as<std::string>("");
            binding.useClips = entry["use_clips"].as<std::vector<std::string>>(std::vector<std::string>{});
            if (entry["animated"])
            {
                const Engine::ModelLoadResult animated = m_assets.load(assets, entry["animated"].as<std::string>());
                if (!animated || animated.asset->clips.empty() || !still || binding.selfAnimated)
                {
                    error = !animated ? animated.error
                        : "decoration animated model needs clips, a still ground binding and a static model: " + name;
                    return false;
                }
                binding.animatedAsset = animated.asset;
            }
            if (m_bindingBySprite.contains(pDecoration->spriteId))
            {
                error = "decoration model bindings share a sprite: " + name;
                return false;
            }
            binding.pickTriangles = pickTriangles(*binding.asset, false);
            binding.billboardPickTriangles = pickTriangles(*binding.asset, true, &binding.billboardPickPivots);
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
                freeStanding->billboardPickTriangles = pickTriangles(*free.asset, true,
                    &freeStanding->billboardPickPivots);
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
                m_groups.push_back({drawn.asset, drawn.materialVariant, drawn.lodPixels, {}, {}, {}, {}});
                m_billboardIndices.emplace_back();
                m_restMatrices.emplace_back();
                if (drawn.swingPeriod > 0.0f)
                {
                    m_swingingGroups.push_back(uint32_t(added));
                }
            }
            if (m_bindings[index].selfAnimated)
            {
                m_selfAnimatedGroups.push_back(index);
            }
            if (m_bindings[index].animatedAsset)
            {
                m_animatedGroups.push_back(index);
            }
            if (!m_bindings[index].useClips.empty())
            {
                m_useGroups.push_back(index);
            }
            // Its moving parts draw into groups of their own, after the bindings they serve.
            if (entry["parts"] && !loadParts(assets, entry, name, index, error))
            {
                return false;
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = "decoration model manifest: " + std::string(exception.what());
        return false;
    }
    if (!loadStateOverlays(assets, worldId, bindingByName, error))
    {
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
