#pragma once

#include <array>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
// The 3D model an item lying on the ground draws (GROUND_ITEMS_3D_PLAN.md); no ground item draws a sprite.
struct ItemModelBinding
{
    // Engine model path. The model lies flat, its longest side along the model's horizontal axes, its underside at 0
    // and its origin at the centre of its footprint.
    std::string model;
    // World units of the model's longest horizontal side; the model is scaled uniformly to it.
    float length = 0.0f;
    // The model's box in world units at that scale, in the item's own frame before its yaw (x across, y along, z up
    // from the origin), written by tools/item_model_shapes.py: the world runtimes collide and pick with it, also
    // headless, where models are never loaded (GROUND_ITEMS_3D_BEHAVIOUR.md).
    std::array<float, 3> boundsMin = {};
    std::array<float, 3> boundsMax = {};
};

// Item icon (items.txt "Pic File", lower case) -> binding: items sharing an icon share a model.
using ItemModelBindings = std::unordered_map<std::string, ItemModelBinding>;

// What an item draws when its icon has no binding or its model fails to load: a spinning magenta and black cube that
// reads as a bug to report and fix, never as art. It is never bound to an icon.
const ItemModelBinding &missingItemModelBinding();

// What a treasure bag on the ground (an MM9 loot container) draws, collides and is picked with: the smallest corpse
// loot satchel. It holds no item of its own, so no icon binds it.
const ItemModelBinding &lootBagModelBinding();

// Reads engine/world_items/items.yml, or a mounted world's worlds/<id>/world_items/items.yml added to the same
// bindings (schema openyamm.itemModels.v1): a list of {icon, model, length, bounds}. A missing file, an unknown key, an
// icon already bound (in this file or an earlier one), a bad length or bad bounds fails.
bool loadItemModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    ItemModelBindings &bindings,
    std::string &error);
// The same from YAML text; path names the source in errors.
bool parseItemModelBindings(const std::string &text, const std::string &path, ItemModelBindings &bindings,
    std::string &error);
}
