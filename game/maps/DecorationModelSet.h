#pragma once

#include "engine/models/GltfModelLoader.h"
#include "engine/render/ModelRenderer.h"
#include "game/maps/DecorationModelPlacement.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
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

// Map decorations drawn as static 3D models, bound by decoration name in worlds/<world>/models/decorations.yml
// (outdoor maps) or indoor_decorations.yml (BLV maps; apart because decorations.yml is an outdoor bake dependency).
// A decoration keeps its native data (collision, events, picking); the sprite it currently shows selects the model, so
// an event SetSprite to another bound decoration (a picked food tree) switches models, and a switch to an unbound
// sprite draws that sprite instead.
class DecorationModelSet
{
public:
    // The wall a decoration (of the given world height) hangs on, if any; indoor maps supply it for mount: wall.
    using WallFinder = std::function<std::optional<DecorationWallContact>(const DecorationBillboard &, float height)>;

    // A world without a manifest loads empty. False with an error for an invalid manifest or model.
    bool load(const Engine::AssetFileSystem &assets, const std::string &worldId, const std::string &mapFile,
        const DecorationBillboardSet &decorations, std::string &error, WallFinder wallFinder = {});
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
    // Whether a model currently draws this billboard (hover and interaction then pick the model, not the sprite).
    bool drawsBillboard(size_t billboardIndex) const
    {
        return billboardIndex < m_slots.size() && m_slots[billboardIndex].group >= 0;
    }
    // Ray against the model a billboard currently shows (its LOD1 triangles, or LOD0 for a model without LODs).
    // distance is the ray parameter (world units for a unit direction). False when nothing is hit or no model draws
    // the billboard; alpha-tested cards count as solid, so a tree crown picks as a whole. Camera-facing cards (flames)
    // are turned toward the ray's origin, where the camera sees them.
    bool raycast(size_t billboardIndex, const std::array<float, 3> &origin, const std::array<float, 3> &direction,
        float &distance) const;
    // Swings the swinging placements (chandeliers, cages) to their pose at timeSeconds.
    void animate(float timeSeconds);
    // Billboards of wall-mounted bindings without a wall in reach or a free_model; they keep their map facing.
    const std::vector<size_t> &unmountedBillboards() const
    {
        return m_unmountedBillboards;
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
        // mount: wall turns the model's back (asset -z) onto the nearest wall face; free_model (its own binding,
        // drawn into its own group) stands where no wall is in reach.
        bool mountWall = false;
        int32_t freeBinding = -1;
        // swing: [angle degrees, period seconds] about the asset x axis through the model's top.
        float swingRadians = 0.0f;
        float swingPeriod = 0.0f;
        // Pick triangles in asset space (three corners each), from LOD1 or LOD0; camera-facing cards apart.
        std::vector<std::array<float, 3>> pickTriangles;
        std::vector<std::array<float, 3>> billboardPickTriangles;
    };
    // Where a billboard's placement lives; group -1 when no model draws it. binding is the binding its sprite
    // selects (group is that binding's free-standing group when no wall was in reach).
    struct Slot
    {
        int32_t group = -1;
        int32_t binding = -1;
        uint32_t index = 0;
        uint16_t sprite = 0;
    };

    // Ray against the placement's rigid (not camera-facing) triangles; lowers best on a nearer hit.
    bool rigidHit(const Slot &slot, const std::array<float, 3> &origin, const std::array<float, 3> &direction,
        float &best) const;
    Engine::ModelStaticPlacement placementFor(const Binding &binding, const DecorationBillboard &billboard,
        const std::optional<DecorationWallContact> &wall) const;
    static float heightJitter(const Binding &binding, const DecorationBillboard &billboard);
    void place(size_t billboardIndex, const DecorationBillboard &billboard, uint32_t binding);
    void unplace(size_t billboardIndex);

    Engine::ModelAssetCache m_assets;
    // Binding i draws into group i.
    std::vector<Binding> m_bindings;
    std::unordered_map<uint16_t, uint32_t> m_bindingBySprite;
    std::vector<Engine::ModelStaticGroup> m_groups;
    std::vector<std::vector<size_t>> m_billboardIndices;
    // Unswung placement matrix of each placement, aligned with the group's placements.
    std::vector<std::vector<Engine::ModelMatrix>> m_restMatrices;
    std::vector<Slot> m_slots;
    WallFinder m_wallFinder;
    std::vector<size_t> m_unmountedBillboards;
    // Groups of swinging bindings.
    std::vector<uint32_t> m_swingingGroups;
};
}
