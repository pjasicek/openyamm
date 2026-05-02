#include "game/content/ContentManifest.h"

#include "game/maps/MapIdentity.h"

#include <yaml-cpp/yaml.h>

#include <exception>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
std::string scalarStringOrDefault(const YAML::Node &node, const char *pKey, const std::string &defaultValue)
{
    const YAML::Node child = node[pKey];

    if (!child || !child.IsScalar())
    {
        return defaultValue;
    }

    return child.as<std::string>();
}

WorldManifest buildDefaultWorldManifest(const std::string &worldId)
{
    WorldManifest manifest = {};
    manifest.id = normalizeWorldId(worldId);
    manifest.name = manifest.id == "mm8" ? "MM8" : manifest.id;
    manifest.sourceGame = manifest.id;
    manifest.start.mapFileName = "out01.odm";
    return manifest;
}

}

WorldManifest loadActiveWorldManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    std::string &errorMessage)
{
    WorldManifest manifest = buildDefaultWorldManifest(worldId);
    const std::optional<std::string> manifestText = assetFileSystem.readTextFile("world.yml");

    if (!manifestText)
    {
        return manifest;
    }

    try
    {
        const YAML::Node root = YAML::Load(*manifestText);

        if (!root || !root.IsMap())
        {
            errorMessage = "world.yml root must be a map";
            return manifest;
        }

        manifest.id = normalizeWorldId(scalarStringOrDefault(root, "id", manifest.id));
        manifest.name = scalarStringOrDefault(root, "name", manifest.name);
        manifest.sourceGame = scalarStringOrDefault(root, "sourceGame", manifest.sourceGame);

        const YAML::Node startNode = root["start"];

        if (startNode && startNode.IsMap())
        {
            manifest.start.mapFileName =
                scalarStringOrDefault(startNode, "map", manifest.start.mapFileName);
            manifest.start.introMovie =
                scalarStringOrDefault(startNode, "introMovie", manifest.start.introMovie);
        }

        manifest.loadedFromFile = true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse world.yml: ") + exception.what();
    }

    return manifest;
}

}
