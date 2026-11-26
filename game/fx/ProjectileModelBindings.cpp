#include "game/fx/ProjectileModelBindings.h"

#include "engine/AssetFileSystem.h"
#include "game/content/ContentManifest.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <limits>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
bool loadProjectileModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    ProjectileModelBindings &bindings,
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
    return parseProjectileModelBindings(*text, path, bindings, error);
}

bool parseProjectileModelBindings(
    const std::string &text,
    const std::string &path,
    ProjectileModelBindings &bindings,
    std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root["schema"] || root["schema"].as<std::string>() != "openyamm.projectileModels.v1" ||
            !root["projectiles"] || !root["projectiles"].IsSequence())
        {
            error = path + ": expected schema openyamm.projectileModels.v1 with a projectiles list";
            return false;
        }
        for (const YAML::Node &entry : root["projectiles"])
        {
            if (!entry.IsMap() || !entry["object"] || !entry["model"] || !entry["length"])
            {
                error = path + ": each projectile needs object, model and length";
                return false;
            }
            const int objectId = entry["object"].as<int>();
            const std::string context = path + ": object " + std::to_string(objectId);
            for (const auto &field : entry)
            {
                const std::string key = field.first.as<std::string>();
                if (key != "object" && key != "model" && key != "length" && key != "spin")
                {
                    error = context + ": unknown key " + key;
                    return false;
                }
            }
            if (objectId <= 0 || objectId > std::numeric_limits<int16_t>::max())
            {
                error = context + ": object must be a positive object id";
                return false;
            }
            ProjectileModelBinding binding;
            binding.sourcePath = path;
            binding.model = entry["model"].as<std::string>();
            binding.length = entry["length"].as<float>();
            if (!std::isfinite(binding.length) || binding.length <= 0.0f)
            {
                error = context + ": length must be a positive number";
                return false;
            }
            if (const YAML::Node spin = entry["spin"])
            {
                const std::string axis = spin.IsMap() && spin["axis"] ? spin["axis"].as<std::string>() : "";
                binding.spinAxis = axis == "forward" ? ProjectileModelSpinAxis::Forward
                    : axis == "up" ? ProjectileModelSpinAxis::Up
                    : axis == "side" ? ProjectileModelSpinAxis::Side
                    : ProjectileModelSpinAxis::None;
                binding.spinDegreesPerSecond =
                    spin.IsMap() && spin["degrees_per_second"] ? spin["degrees_per_second"].as<float>() : 0.0f;
                if (binding.spinAxis == ProjectileModelSpinAxis::None || spin.size() != 2 ||
                    !std::isfinite(binding.spinDegreesPerSecond) || binding.spinDegreesPerSecond == 0.0f)
                {
                    error = context + ": spin needs axis (forward, up or side) and a non-zero degrees_per_second";
                    return false;
                }
            }
            if (!bindings.emplace(int16_t(objectId), std::move(binding)).second)
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

bool mergeWorldProjectileModelBindings(
    const std::string &text,
    const std::string &path,
    uint32_t objectBegin,
    uint32_t objectEnd,
    ProjectileModelBindings &bindings,
    std::string &error)
{
    ProjectileModelBindings added;
    if (!parseProjectileModelBindings(text, path, added, error))
    {
        return false;
    }
    for (const auto &[objectId, binding] : added)
    {
        const std::string context = path + ": object " + std::to_string(objectId);
        if (uint32_t(objectId) < objectBegin || uint32_t(objectId) > objectEnd)
        {
            error = context + " is outside the world's objects id range";
            return false;
        }
        if (const auto found = bindings.find(objectId); found != bindings.end())
        {
            error = context + " is already bound by " + found->second.sourcePath;
            return false;
        }
    }
    bindings.merge(added);
    return true;
}

bool loadAllProjectileModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    ProjectileModelBindings &bindings,
    std::string &error)
{
    if (!loadProjectileModelBindings(assetFileSystem, "engine/models/projectiles.yml", bindings, error))
    {
        return false;
    }
    std::vector<WorldManifest> mountedWorlds;
    if (!loadMountedWorldManifests(assetFileSystem, mountedWorlds, error))
    {
        return false;
    }
    for (const WorldManifest &manifest : mountedWorlds)
    {
        const std::string path = "worlds/" + manifest.id + "/models/projectiles.yml";
        if (!assetFileSystem.exists(path))
        {
            continue;
        }
        const ContentIdRangeDefinition *pObjectRange = manifest.findIdRange("objects");
        if (pObjectRange == nullptr)
        {
            error = path + ": the world needs an objects id range";
            return false;
        }
        const std::optional<std::string> text = assetFileSystem.readTextFile(path);
        if (!text)
        {
            error = path + ": unreadable";
            return false;
        }
        if (!mergeWorldProjectileModelBindings(
                *text, path, pObjectRange->begin, pObjectRange->end, bindings, error))
        {
            return false;
        }
    }
    return true;
}
}
