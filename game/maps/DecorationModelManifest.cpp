#include "game/maps/DecorationModelManifest.h"

#include "engine/AssetFileSystem.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
std::vector<std::string> manifestPaths(const std::string &worldId, const std::string &fileName)
{
    return {"engine/models/" + fileName, "worlds/" + worldId + "/models/" + fileName};
}

// The entries of the manifests in order; a later manifest's entry for a name replaces the earlier entries of that
// name, and one whose payload (model, or overlay states) is null removes them.
bool mergedManifestEntries(const Engine::AssetFileSystem &assets, const std::vector<std::string> &paths,
    const std::string &sequenceKey, const std::string &payloadKey, std::vector<YAML::Node> &entries,
    std::string &error)
{
    entries.clear();
    for (size_t pathIndex = 0; pathIndex < paths.size(); ++pathIndex)
    {
        const std::optional<std::string> text = assets.readTextFile(paths[pathIndex]);
        if (!text)
        {
            continue;
        }
        try
        {
            const YAML::Node document = YAML::Load(*text);
            if (!document[sequenceKey].IsSequence())
            {
                error = "decoration manifest requires a " + sequenceKey + " sequence: " + paths[pathIndex];
                return false;
            }
            std::vector<YAML::Node> added;
            for (const YAML::Node &entry : document[sequenceKey])
            {
                added.push_back(entry);
            }
            if (pathIndex > 0)
            {
                std::vector<std::string> replaced;
                for (const YAML::Node &entry : added)
                {
                    replaced.push_back(toLowerCopy(entry["name"].as<std::string>()));
                }
                // Filtered into a new vector: assigning a YAML::Node (as erase_if would) overwrites the node it
                // refers to instead of rebinding it.
                std::vector<YAML::Node> kept;
                for (const YAML::Node &earlier : entries)
                {
                    if (std::find(replaced.begin(), replaced.end(), toLowerCopy(earlier["name"].as<std::string>()))
                        == replaced.end())
                    {
                        kept.push_back(earlier);
                    }
                }
                entries.swap(kept);
            }
            for (const YAML::Node &entry : added)
            {
                if (!entry[payloadKey].IsNull())
                {
                    entries.push_back(entry);
                }
            }
        }
        catch (const YAML::Exception &exception)
        {
            error = paths[pathIndex] + ": " + exception.what();
            return false;
        }
    }
    return true;
}
}

std::vector<std::string> decorationModelManifestPaths(const std::string &worldId, const std::string &mapFile)
{
    const bool indoor = toLowerCopy(mapFile).ends_with(".blv");
    return manifestPaths(worldId, indoor ? "indoor_decorations.yml" : "decorations.yml");
}

std::vector<std::string> decorationOverlayManifestPaths(const std::string &worldId)
{
    return manifestPaths(worldId, "decoration_overlays.yml");
}

bool decorationModelBindsOnMap(const YAML::Node &entry, const std::string &mapFile)
{
    if (!entry["maps"])
    {
        return true;
    }
    const std::string lowerMap = toLowerCopy(mapFile);
    const std::vector<std::string> maps = entry["maps"].as<std::vector<std::string>>();
    return std::any_of(maps.begin(), maps.end(),
        [&](const std::string &map) { return toLowerCopy(map) == lowerMap; });
}

bool decorationModelEntries(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile, std::vector<YAML::Node> &entries, std::string &error)
{
    if (!mergedManifestEntries(assets, decorationModelManifestPaths(worldId, mapFile), "decorations", "model",
            entries, error))
    {
        return false;
    }
    try
    {
        std::vector<YAML::Node> binding;
        for (const YAML::Node &entry : entries)
        {
            if (decorationModelBindsOnMap(entry, mapFile))
            {
                binding.push_back(entry);
            }
        }
        entries.swap(binding);
    }
    catch (const YAML::Exception &exception)
    {
        error = "decoration model manifest maps: " + std::string(exception.what());
        return false;
    }
    return true;
}

bool decorationOverlayEntries(const Engine::AssetFileSystem &assets, const std::string &worldId,
    std::vector<YAML::Node> &entries, std::string &error)
{
    return mergedManifestEntries(assets, decorationOverlayManifestPaths(worldId), "overlays", "states", entries,
        error);
}

bool modelledDecorationNames(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile, std::vector<std::string> &names, std::string &error)
{
    names.clear();
    std::vector<YAML::Node> entries;
    if (!decorationModelEntries(assets, worldId, mapFile, entries, error))
    {
        return false;
    }
    try
    {
        for (const YAML::Node &entry : entries)
        {
            names.push_back(toLowerCopy(entry["name"].as<std::string>()));
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = "decoration model manifest names: " + std::string(exception.what());
        return false;
    }
    return true;
}

std::unordered_set<std::string> mapEventSpriteNames(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const std::string &mapFile)
{
    // The map's script and its overlays (<map>_*.lua), as the event runtime loads them, and the world's common scripts
    // (events/common/*.lua), which every map of the world runs (Hesper's pickups swap their sprites there).
    const std::string directory = "worlds/" + worldId + "/events/maps";
    const std::string stem = toLowerCopy(std::filesystem::path(mapFile).stem().string());
    std::vector<std::string> scripts = {directory + "/" + stem + ".lua"};
    for (const std::string &entry : assets.enumerate(directory))
    {
        const std::string lowerEntry = toLowerCopy(entry);
        if (lowerEntry.starts_with(stem + "_") && lowerEntry.ends_with(".lua"))
        {
            scripts.push_back(directory + "/" + entry);
        }
    }
    const std::string commonDirectory = "worlds/" + worldId + "/events/common";
    for (const std::string &entry : assets.enumerate(commonDirectory))
    {
        if (toLowerCopy(entry).ends_with(".lua"))
        {
            scripts.push_back(commonDirectory + "/" + entry);
        }
    }
    std::unordered_set<std::string> names;
    for (const std::string &script : scripts)
    {
        const std::optional<std::string> text = assets.readTextFile(script);
        if (!text)
        {
            continue;
        }
        // SetSprite(cog, setting, "name"): the third argument when it is a string literal.
        static const std::string Call = "SetSprite(";
        for (size_t found = text->find(Call); found != std::string::npos; found = text->find(Call, found + 1))
        {
            size_t cursor = found + Call.size();
            int commas = 0;
            while (cursor < text->size() && commas < 2 && (*text)[cursor] != ')' && (*text)[cursor] != '\n')
            {
                commas += (*text)[cursor] == ',' ? 1 : 0;
                ++cursor;
            }
            while (cursor < text->size() && (*text)[cursor] == ' ')
            {
                ++cursor;
            }
            if (commas != 2 || cursor >= text->size() || (*text)[cursor] != '"')
            {
                continue;
            }
            const size_t end = text->find('"', cursor + 1);
            if (end != std::string::npos)
            {
                names.insert(toLowerCopy(text->substr(cursor + 1, end - cursor - 1)));
            }
        }
    }
    return names;
}
}
