#include "game/tables/ItemModelBindings.h"

#include "engine/AssetFileSystem.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>

namespace OpenYAMM::Game
{
const ItemModelBinding &missingItemModelBinding()
{
    static const ItemModelBinding binding = {
        .model = "engine/world_items/models/missing_item.glb",
        .length = 40.0f,
        .boundsMin = {-20.0f, -20.0f, 0.0f},
        .boundsMax = {20.0f, 20.0f, 40.0f},
    };
    return binding;
}

const ItemModelBinding &lootBagModelBinding()
{
    // At the corpse satchel's size (0.5 m at 105 units a metre); bounds measured as tools/item_model_shapes.py does.
    static const ItemModelBinding binding = {
        .model = "engine/models/loot_satchel_t1.glb",
        .length = 52.5f,
        .boundsMin = {-26.2f, -25.5f, 0.0f},
        .boundsMax = {26.2f, 25.5f, 53.3f},
    };
    return binding;
}

bool loadItemModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    ItemModelBindings &bindings,
    std::string &error)
{
    const std::optional<std::string> text = assetFileSystem.readTextFile(path);
    if (!text)
    {
        error = path + ": missing or unreadable";
        return false;
    }
    return parseItemModelBindings(*text, path, bindings, error);
}

bool parseItemModelBindings(const std::string &text, const std::string &path, ItemModelBindings &bindings,
    std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root["schema"] || root["schema"].as<std::string>() != "openyamm.itemModels.v1" || !root["items"]
            || !root["items"].IsSequence())
        {
            error = path + ": expected schema openyamm.itemModels.v1 with an items list";
            return false;
        }
        for (const YAML::Node &entry : root["items"])
        {
            if (!entry.IsMap() || !entry["icon"] || !entry["model"] || !entry["length"] || !entry["bounds"])
            {
                error = path + ": each item needs icon, model, length and bounds";
                return false;
            }
            std::string icon = entry["icon"].as<std::string>();
            std::transform(icon.begin(), icon.end(), icon.begin(),
                [](unsigned char character)
                {
                    return char(std::tolower(character));
                });
            const std::string context = path + ": icon " + icon;
            for (const auto &field : entry)
            {
                const std::string key = field.first.as<std::string>();
                if (key != "icon" && key != "model" && key != "length" && key != "bounds")
                {
                    error = context + ": unknown key " + key;
                    return false;
                }
            }
            ItemModelBinding binding;
            binding.model = entry["model"].as<std::string>();
            binding.length = entry["length"].as<float>();
            if (icon.empty() || !std::isfinite(binding.length) || binding.length <= 0.0f)
            {
                error = context + ": needs an icon and a positive length";
                return false;
            }
            const YAML::Node bounds = entry["bounds"];
            if (!bounds.IsSequence() || bounds.size() != 6)
            {
                error = context + ": bounds needs [minX, minY, minZ, maxX, maxY, maxZ]";
                return false;
            }
            for (size_t axis = 0; axis < 3; ++axis)
            {
                binding.boundsMin[axis] = bounds[axis].as<float>();
                binding.boundsMax[axis] = bounds[axis + 3].as<float>();
                if (!std::isfinite(binding.boundsMin[axis]) || !std::isfinite(binding.boundsMax[axis])
                    || binding.boundsMax[axis] < binding.boundsMin[axis])
                {
                    error = context + ": bounds needs finite minimums no larger than their maximums";
                    return false;
                }
            }
            if (!bindings.emplace(icon, std::move(binding)).second)
            {
                error = context + ": bound twice";
                return false;
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = path + ": " + exception.what();
        return false;
    }
    return true;
}
}
