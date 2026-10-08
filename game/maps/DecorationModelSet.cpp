#include "game/maps/DecorationModelSet.h"

#include "engine/AssetFileSystem.h"
#include "game/maps/MapAssetLoader.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <numbers>
#include <optional>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
std::string lowercase(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char value) { return char(std::tolower(value)); });
    return text;
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
    m_slots.clear();
    m_assets.clear();
}

Engine::ModelStaticPlacement DecorationModelSet::placementFor(const Binding &binding,
    const DecorationBillboard &billboard) const
{
    const Engine::ModelBounds &bounds = binding.asset->staticBounds;
    const float jitter = 1.0f + binding.heightJitter * (2.0f * placementRandom(billboard.x, billboard.y, 1) - 1.0f);
    const float scale = binding.height / (bounds.max[1] - bounds.min[1]) * jitter;
    const float yaw = (binding.randomYaw ? placementRandom(billboard.x, billboard.y, 2) * 2.0f * std::numbers::pi_v<float>
        : float(billboard.facing) * std::numbers::pi_v<float> / 180.0f) + binding.yawOffset;
    Engine::ModelStaticPlacement placement;
    placement.matrix = Engine::composeModelTransform(Engine::gltfModelPlacement(
        {float(billboard.x), float(billboard.y), float(billboard.z) + binding.zOffset}, yaw, scale));
    return placement;
}

void DecorationModelSet::place(size_t billboardIndex, const DecorationBillboard &billboard, uint32_t binding)
{
    Engine::ModelStaticGroup &group = m_groups[binding];
    group.placements.push_back(placementFor(m_bindings[binding], billboard));
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
    swapRemove(indices);
    group.placements[slot.index] = group.placements[last];
    group.placements.pop_back();
    if (slot.index < indices.size())
    {
        m_slots[indices[slot.index]].index = slot.index;
    }
    slot.group = -1;
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
            if (target != slot.group)
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

bool DecorationModelSet::load(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile, const DecorationBillboardSet &decorations, std::string &error)
{
    clear();
    const std::string manifestPath = "worlds/" + worldId + "/models/decorations.yml";
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
            const uint32_t index = uint32_t(m_bindings.size());
            bindingByName.emplace(name, index);
            m_bindingBySprite.emplace(pDecoration->spriteId, index);
            m_groups.push_back({binding.asset, 0, binding.lodPixels, {}, {}, {}, {}});
            m_billboardIndices.emplace_back();
            m_bindings.push_back(std::move(binding));
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
