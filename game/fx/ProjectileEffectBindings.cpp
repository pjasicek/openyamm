#include "game/fx/ProjectileEffectBindings.h"

#include "engine/AssetFileSystem.h"
#include "game/fx/EffectSystem.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
bool readEffectId(
    const YAML::Node &node,
    const char *pKey,
    const EffectLibrary &library,
    const std::string &context,
    std::string &effectId,
    std::string &error)
{
    if (!node[pKey])
    {
        return true;
    }
    effectId = node[pKey].as<std::string>();
    if (library.find(effectId) == nullptr)
    {
        error = context + ": unknown " + pKey + " effect " + effectId;
        return false;
    }
    return true;
}

// Reads the binding fields of a recipe entry or a variant over the given defaults.
bool readBinding(
    const YAML::Node &node,
    const EffectLibrary &library,
    const std::string &context,
    bool variant,
    ProjectileEffectBinding &binding,
    std::string &error,
    bool object = false)
{
    for (const auto &entry : node)
    {
        const std::string key = entry.first.as<std::string>();
        const bool known = key == "flight" || key == "settled" || key == "impact" || key == "impact_follows_target" ||
            key == "return_flight" || key == "sprite" || key == "light" || (object && key == "impact_light") ||
            (!object && (variant ? key == "monsters" : key == "variants"));
        if (!known)
        {
            error = context + ": unknown key " + key;
            return false;
        }
    }
    if (!readEffectId(node, "flight", library, context, binding.flight, error) ||
        !readEffectId(node, "settled", library, context, binding.settled, error) ||
        !readEffectId(node, "impact", library, context, binding.impact, error) ||
        !readEffectId(node, "return_flight", library, context, binding.returnFlight, error))
    {
        return false;
    }
    if (node["impact_follows_target"])
    {
        binding.impactFollowsTarget = node["impact_follows_target"].as<bool>();
    }
    if (node["sprite"])
    {
        const std::string sprite = node["sprite"].as<std::string>();
        if (sprite != "native" && sprite != "hidden")
        {
            error = context + ": sprite must be native or hidden";
            return false;
        }
        binding.nativeSprite = sprite == "native";
    }
    for (const char *pKey : {"light", "impact_light"})
    {
        const YAML::Node light = node[pKey];
        if (!light)
        {
            continue;
        }
        if (!light.IsMap() || !light["rgb"] || !light["rgb"].IsSequence() || light["rgb"].size() != 3 ||
            !light["radius"])
        {
            error = context + ": " + pKey + " needs rgb [r, g, b] and radius";
            return false;
        }
        ProjectileEffectLight value;
        for (size_t channel = 0; channel < 3; ++channel)
        {
            value.rgb[channel] = uint8_t(std::clamp(light["rgb"][channel].as<int>(), 0, 255));
        }
        value.radius = light["radius"].as<float>();
        if (!std::isfinite(value.radius) || value.radius < 0.0f)
        {
            error = context + ": " + pKey + " radius must be a non-negative number";
            return false;
        }
        (std::string(pKey) == "light" ? binding.light : binding.impactLight) = value;
    }
    return true;
}
}

const ProjectileEffectBinding *ProjectileEffectBindings::find(
    FxRecipes::ProjectileRecipe recipe,
    const std::string &monsterPicture,
    const std::string &objectName) const
{
    if (!objectName.empty() && !m_objects.empty())
    {
        const auto object = m_objects.find(normalizeMonsterPicture(objectName));
        if (object != m_objects.end())
        {
            return &object->second;
        }
    }
    if (!monsterPicture.empty())
    {
        const auto variants = m_variants.find(recipe);
        if (variants != m_variants.end())
        {
            const auto variant = variants->second.find(normalizeMonsterPicture(monsterPicture));
            if (variant != variants->second.end())
            {
                return &variant->second;
            }
        }
    }
    const auto it = m_recipes.find(recipe);
    return it != m_recipes.end() ? &it->second : nullptr;
}

bool ProjectileEffectBindings::contains(FxRecipes::ProjectileRecipe recipe) const
{
    return m_recipes.contains(recipe);
}

bool ProjectileEffectBindings::empty() const
{
    return m_recipes.empty() && m_variants.empty() && m_objects.empty();
}

std::vector<std::string> ProjectileEffectBindings::objectNames() const
{
    std::vector<std::string> names;
    for (const auto &[name, binding] : m_objects)
    {
        names.push_back(name);
    }
    std::sort(names.begin(), names.end());
    return names;
}

std::vector<std::string> ProjectileEffectBindings::variantMonsterPictures() const
{
    std::vector<std::string> pictures;
    for (const auto &[recipe, variants] : m_variants)
    {
        for (const auto &[picture, binding] : variants)
        {
            pictures.push_back(picture);
        }
    }
    std::sort(pictures.begin(), pictures.end());
    pictures.erase(std::unique(pictures.begin(), pictures.end()), pictures.end());
    return pictures;
}

std::vector<std::string> ProjectileEffectBindings::effectIds() const
{
    std::vector<std::string> ids;
    const auto add = [&](const ProjectileEffectBinding &binding)
    {
        for (const std::string *pId : {&binding.flight, &binding.settled, &binding.impact, &binding.returnFlight})
        {
            if (!pId->empty())
            {
                ids.push_back(*pId);
            }
        }
    };
    for (const auto &[recipe, binding] : m_recipes)
    {
        add(binding);
    }
    for (const auto &[recipe, variants] : m_variants)
    {
        for (const auto &[picture, binding] : variants)
        {
            add(binding);
        }
    }
    for (const auto &[name, binding] : m_objects)
    {
        add(binding);
    }
    if (!m_waterSplash.empty())
    {
        ids.push_back(m_waterSplash);
    }
    std::sort(ids.begin(), ids.end());
    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
    return ids;
}

void ProjectileEffectBindings::setRecipe(FxRecipes::ProjectileRecipe recipe, ProjectileEffectBinding binding)
{
    m_recipes[recipe] = std::move(binding);
}

void ProjectileEffectBindings::setObject(const std::string &objectName, ProjectileEffectBinding binding)
{
    m_objects[normalizeMonsterPicture(objectName)] = std::move(binding);
}

void ProjectileEffectBindings::setVariant(
    FxRecipes::ProjectileRecipe recipe,
    const std::string &monsterPicture,
    ProjectileEffectBinding binding)
{
    m_variants[recipe][normalizeMonsterPicture(monsterPicture)] = std::move(binding);
}

std::string ProjectileEffectBindings::normalizeMonsterPicture(const std::string &monsterPicture)
{
    const size_t first = monsterPicture.find_first_not_of(" \t");
    const size_t last = monsterPicture.find_last_not_of(" \t");
    std::string normalized =
        first == std::string::npos ? std::string() : monsterPicture.substr(first, last - first + 1);
    std::transform(normalized.begin(), normalized.end(), normalized.begin(),
        [](unsigned char character)
        {
            return char(std::tolower(character));
        });
    return normalized;
}

bool loadProjectileEffectBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    const EffectLibrary &library,
    ProjectileEffectBindings &bindings,
    std::string &error)
{
    if (!assetFileSystem.exists(path))
    {
        return true;
    }
    const std::optional<std::string> text = assetFileSystem.readTextFile(path);
    if (!text)
    {
        error = path + ": unreadable";
        return false;
    }
    return parseProjectileEffectBindings(*text, path, library, bindings, error);
}

bool parseProjectileEffectBindings(
    const std::string &text,
    const std::string &path,
    const EffectLibrary &library,
    ProjectileEffectBindings &bindings,
    std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root["schema"] || root["schema"].as<std::string>() != "openyamm.projectileEffects.v1" ||
            !root["projectiles"] || !root["projectiles"].IsMap())
        {
            error = path + ": expected schema openyamm.projectileEffects.v1 with a projectiles map";
            return false;
        }
        if (const YAML::Node objects = root["objects"])
        {
            if (!objects.IsMap())
            {
                error = path + ": objects must map object names to bindings";
                return false;
            }
            for (const auto &entry : objects)
            {
                const std::string objectName = entry.first.as<std::string>();
                const std::string context = path + ": object " + objectName;
                ProjectileEffectBinding binding;
                if (!entry.second.IsMap() || !readBinding(entry.second, library, context, false, binding, error, true))
                {
                    error = error.empty() ? context + ": expected a binding map" : error;
                    return false;
                }
                if (binding.flight.empty() || binding.impact.empty())
                {
                    error = context + ": an object binding names a flight and an impact effect";
                    return false;
                }
                bindings.setObject(objectName, std::move(binding));
            }
        }
        if (root["water_splash"])
        {
            std::string effectId;
            if (!readEffectId(root, "water_splash", library, path, effectId, error))
            {
                return false;
            }
            bindings.setWaterSplash(std::move(effectId));
        }
        for (const auto &entry : root["projectiles"])
        {
            const std::string recipeName = entry.first.as<std::string>();
            const std::string context = path + ": " + recipeName;
            const std::optional<FxRecipes::ProjectileRecipe> recipe = FxRecipes::projectileRecipeFromName(recipeName);
            if (!recipe || *recipe == FxRecipes::ProjectileRecipe::None || !entry.second.IsMap())
            {
                error = path + ": unknown projectile recipe " + recipeName;
                return false;
            }
            ProjectileEffectBinding binding;
            if (!readBinding(entry.second, library, context, false, binding, error))
            {
                return false;
            }
            if (binding.flight.empty() && binding.settled.empty() && binding.impact.empty() && !binding.nativeSprite)
            {
                error = context + ": names no flight, settled or impact effect and no sprite";
                return false;
            }
            if (const YAML::Node variants = entry.second["variants"])
            {
                if (!variants.IsSequence())
                {
                    error = context + ": variants must be a list";
                    return false;
                }
                for (const YAML::Node &variantNode : variants)
                {
                    const YAML::Node monsters = variantNode["monsters"];
                    if (!variantNode.IsMap() || !monsters || !monsters.IsSequence() || monsters.size() == 0)
                    {
                        error = context + ": each variant needs a monsters list";
                        return false;
                    }
                    ProjectileEffectBinding variant = binding;
                    if (!readBinding(variantNode, library, context + " variant", true, variant, error))
                    {
                        return false;
                    }
                    for (const YAML::Node &monster : monsters)
                    {
                        bindings.setVariant(*recipe, monster.as<std::string>(), variant);
                    }
                }
            }
            bindings.setRecipe(*recipe, std::move(binding));
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
