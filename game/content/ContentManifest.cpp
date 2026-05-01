#include "game/content/ContentManifest.h"

#include "game/maps/MapIdentity.h"

#include <yaml-cpp/yaml.h>

#include <exception>
#include <optional>
#include <string>
#include <vector>

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

std::vector<std::string> stringSequenceOrDefault(
    const YAML::Node &node,
    const char *pKey,
    const std::vector<std::string> &defaultValue)
{
    const YAML::Node child = node[pKey];

    if (!child || !child.IsSequence())
    {
        return defaultValue;
    }

    std::vector<std::string> values;

    for (const YAML::Node &entry : child)
    {
        if (entry.IsScalar())
        {
            values.push_back(entry.as<std::string>());
        }
    }

    return values.empty() ? defaultValue : values;
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

CampaignManifest buildDefaultCampaignManifest(const std::string &campaignId, const std::string &activeWorldId)
{
    CampaignManifest manifest = {};
    manifest.id = campaignId.empty() ? "default" : campaignId;
    manifest.name = "Default Campaign";
    manifest.worlds = {normalizeWorldId(activeWorldId)};
    manifest.startWorlds = manifest.worlds;
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

CampaignManifest loadCampaignManifestOrDefault(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &campaignId,
    const std::string &activeWorldId,
    std::string &errorMessage)
{
    CampaignManifest manifest = buildDefaultCampaignManifest(campaignId, activeWorldId);
    const std::string normalizedCampaignId = campaignId.empty() ? "default" : campaignId;
    const std::optional<std::string> manifestText =
        assetFileSystem.readTextFile("campaigns/" + normalizedCampaignId + "/campaign.yml");

    if (!manifestText)
    {
        return manifest;
    }

    try
    {
        const YAML::Node root = YAML::Load(*manifestText);

        if (!root || !root.IsMap())
        {
            errorMessage = "campaign.yml root must be a map";
            return manifest;
        }

        manifest.id = scalarStringOrDefault(root, "id", manifest.id);
        manifest.name = scalarStringOrDefault(root, "name", manifest.name);
        manifest.worlds = stringSequenceOrDefault(root, "worlds", manifest.worlds);
        manifest.startWorlds = stringSequenceOrDefault(root, "startWorlds", manifest.startWorlds);
        manifest.loadedFromFile = true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse campaign.yml: ") + exception.what();
    }

    return manifest;
}
}
