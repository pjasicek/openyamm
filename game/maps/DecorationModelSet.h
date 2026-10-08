#pragma once

#include "engine/models/GltfModelLoader.h"
#include "engine/render/ModelRenderer.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
struct DecorationBillboard;
struct DecorationBillboardSet;

// Map decorations drawn as static 3D models, bound by decoration name in worlds/<world>/models/decorations.yml.
// A decoration keeps its native data (collision, events, picking); the sprite it currently shows selects the model, so
// an event SetSprite to another bound decoration (a picked food tree) switches models, and a switch to an unbound
// sprite draws that sprite instead.
class DecorationModelSet
{
public:
    // A world without a manifest loads empty. False with an error for an invalid manifest or model.
    bool load(const Engine::AssetFileSystem &assets, const std::string &worldId, const std::string &mapFile,
        const DecorationBillboardSet &decorations, std::string &error);
    void clear();
    bool empty() const
    {
        return m_bindings.empty();
    }
    // Event state of every decoration billboard: the sprite it shows now (0 = none) and whether it is hidden.
    // Moves placements between models when the shown sprite changes and sets placement visibility.
    void update(const std::vector<DecorationBillboard> &billboards,
        const std::function<uint16_t(size_t billboardIndex, bool &hidden)> &shownSprite);
    // True when a model draws this sprite (its billboard must not be drawn).
    bool modelsSprite(uint16_t spriteId) const
    {
        return m_bindingBySprite.contains(spriteId);
    }
    std::vector<Engine::ModelStaticGroup> &groups()
    {
        return m_groups;
    }
    const std::vector<Engine::ModelStaticGroup> &groups() const
    {
        return m_groups;
    }
    // Billboard index of each placement of a group.
    const std::vector<size_t> &billboardIndices(size_t group) const
    {
        return m_billboardIndices[group];
    }

private:
    struct Binding
    {
        std::shared_ptr<const Engine::ModelAsset> asset;
        float height = 0.0f;
        float heightJitter = 0.0f;
        bool randomYaw = true;
        float yawOffset = 0.0f;
        float zOffset = 0.0f;
        std::array<float, 3> lodPixels = Engine::ModelLodPixels;
    };
    // Where a billboard's placement lives; group -1 when no model draws it.
    struct Slot
    {
        int32_t group = -1;
        uint32_t index = 0;
        uint16_t sprite = 0;
    };

    Engine::ModelStaticPlacement placementFor(const Binding &binding, const DecorationBillboard &billboard) const;
    void place(size_t billboardIndex, const DecorationBillboard &billboard, uint32_t binding);
    void unplace(size_t billboardIndex);

    Engine::ModelAssetCache m_assets;
    // Binding i draws into group i.
    std::vector<Binding> m_bindings;
    std::unordered_map<uint16_t, uint32_t> m_bindingBySprite;
    std::vector<Engine::ModelStaticGroup> m_groups;
    std::vector<std::vector<size_t>> m_billboardIndices;
    std::vector<Slot> m_slots;
};
}
