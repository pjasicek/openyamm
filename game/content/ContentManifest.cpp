#include "game/content/ContentManifest.h"

#include "game/StringUtils.h"
#include "game/maps/MapIdentity.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <exception>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_set>

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

uint32_t scalarUint32OrDefault(const YAML::Node &node, const char *pKey, uint32_t defaultValue)
{
    const YAML::Node child = node[pKey];
    return child && child.IsScalar() ? child.as<uint32_t>() : defaultValue;
}

std::string normalizedToken(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
}

bool isSafePackageRelativePath(const std::string &path)
{
    if (path.empty())
    {
        return false;
    }

    const std::filesystem::path parsedPath(path);

    if (parsedPath.is_absolute())
    {
        return false;
    }

    for (const std::filesystem::path &component : parsedPath)
    {
        if (component == "..")
        {
            return false;
        }
    }

    return true;
}

std::optional<TableContributionMode> parseContributionMode(const std::string &value)
{
    const std::string normalized = normalizedToken(value);

    if (normalized == "append")
    {
        return TableContributionMode::Append;
    }

    if (normalized == "override")
    {
        return TableContributionMode::Override;
    }

    if (normalized == "distribution")
    {
        return TableContributionMode::Distribution;
    }

    return std::nullopt;
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

bool parseManifestRoot(const YAML::Node &root, WorldManifest &manifest, std::string &errorMessage)
{
    if (!root || !root.IsMap())
    {
        errorMessage = "world.yml root must be a map";
        return false;
    }

    manifest.id = normalizeWorldId(scalarStringOrDefault(root, "id", manifest.id));
    manifest.name = scalarStringOrDefault(root, "name", manifest.name);
    manifest.sourceGame = scalarStringOrDefault(root, "sourceGame", manifest.sourceGame);
    manifest.contentSchemaVersion = scalarUint32OrDefault(root, "contentSchemaVersion", 1);

    if (manifest.contentSchemaVersion == 0)
    {
        errorMessage = "world.yml contentSchemaVersion must be non-zero";
        return false;
    }

    const YAML::Node startNode = root["start"];

    if (startNode && startNode.IsMap())
    {
        manifest.start.mapFileName = scalarStringOrDefault(startNode, "map", manifest.start.mapFileName);
        manifest.start.introMovie = scalarStringOrDefault(startNode, "introMovie", manifest.start.introMovie);
    }

    const YAML::Node qbitsNode = root["qbits"];
    if (qbitsNode && qbitsNode.IsMap())
    {
        manifest.qbits.begin = scalarUint32OrDefault(qbitsNode, "begin", 0);
        manifest.qbits.end = scalarUint32OrDefault(qbitsNode, "end", 0);
        manifest.qbits.mapping = scalarStringOrDefault(qbitsNode, "mapping", {});
        manifest.qbits.declared = manifest.qbits.begin != 0 || manifest.qbits.end != 0;

        if (!manifest.qbits.declared || manifest.qbits.begin > manifest.qbits.end)
        {
            errorMessage = "world.yml qbits range must declare an ordered, non-zero begin and end";
            return false;
        }
    }

    const YAML::Node partyMovementNode = root["partyMovement"];
    if (partyMovementNode)
    {
        if (!partyMovementNode.IsMap())
        {
            errorMessage = "world.yml partyMovement must declare eyeHeight, collisionRadius, and collisionHeight";
            return false;
        }

        const YAML::Node eyeHeightNode = partyMovementNode["eyeHeight"];
        const YAML::Node collisionRadiusNode = partyMovementNode["collisionRadius"];
        const YAML::Node collisionHeightNode = partyMovementNode["collisionHeight"];
        const YAML::Node maxStepHeightNode = partyMovementNode["maxStepHeight"];

        if (!eyeHeightNode || !eyeHeightNode.IsScalar()
            || !collisionRadiusNode || !collisionRadiusNode.IsScalar()
            || !collisionHeightNode || !collisionHeightNode.IsScalar())
        {
            errorMessage = "world.yml partyMovement must declare eyeHeight, collisionRadius, and collisionHeight";
            return false;
        }

        manifest.partyMovement.eyeHeight = eyeHeightNode.as<float>();
        manifest.partyMovement.collisionRadius = collisionRadiusNode.as<float>();
        manifest.partyMovement.collisionHeight = collisionHeightNode.as<float>();
        if (maxStepHeightNode)
        {
            if (!maxStepHeightNode.IsScalar())
            {
                errorMessage = "world.yml partyMovement maxStepHeight must be scalar";
                return false;
            }

            manifest.partyMovement.maxStepHeight = maxStepHeightNode.as<float>();
        }
        manifest.partyMovement.declared = true;

        if (!std::isfinite(manifest.partyMovement.eyeHeight)
            || !std::isfinite(manifest.partyMovement.collisionRadius)
            || !std::isfinite(manifest.partyMovement.collisionHeight)
            || !std::isfinite(manifest.partyMovement.maxStepHeight)
            || manifest.partyMovement.eyeHeight <= 0.0f
            || manifest.partyMovement.collisionRadius <= 0.0f
            || manifest.partyMovement.collisionHeight <= 0.0f
            || manifest.partyMovement.maxStepHeight <= 0.0f
            || manifest.partyMovement.eyeHeight > manifest.partyMovement.collisionHeight)
        {
            errorMessage =
                "world.yml partyMovement dimensions must be finite and positive, "
                "with eyeHeight at most collisionHeight";
            return false;
        }
    }

    const YAML::Node actorAwarenessNode = root["actorAwareness"];
    if (actorAwarenessNode)
    {
        if (!actorAwarenessNode.IsMap())
        {
            errorMessage = "world.yml actorAwareness must declare partyEngagementRange";
            return false;
        }

        const YAML::Node partyEngagementRangeNode = actorAwarenessNode["partyEngagementRange"];
        if (!partyEngagementRangeNode || !partyEngagementRangeNode.IsScalar())
        {
            errorMessage = "world.yml actorAwareness must declare partyEngagementRange";
            return false;
        }

        manifest.actorAwareness.partyEngagementRange = partyEngagementRangeNode.as<float>();
        manifest.actorAwareness.declared = true;

        if (!std::isfinite(manifest.actorAwareness.partyEngagementRange)
            || manifest.actorAwareness.partyEngagementRange <= 0.0f)
        {
            errorMessage = "world.yml actorAwareness partyEngagementRange must be finite and positive";
            return false;
        }
    }

    if (const YAML::Node actorCombatNode = root["actorCombat"])
    {
        const YAML::Node reachNode = actorCombatNode.IsMap() ? actorCombatNode["meleeVerticalReach"] : YAML::Node();
        if (!reachNode || !reachNode.IsScalar())
        {
            errorMessage = "world.yml actorCombat must declare meleeVerticalReach";
            return false;
        }

        manifest.actorCombat.meleeVerticalReach = reachNode.as<float>();

        if (!std::isfinite(manifest.actorCombat.meleeVerticalReach)
            || manifest.actorCombat.meleeVerticalReach < 0.0f || manifest.actorCombat.meleeVerticalReach > 4.0f)
        {
            errorMessage = "world.yml actorCombat meleeVerticalReach must be a number in 0-4";
            return false;
        }
    }

    if (const YAML::Node actorMovementNode = root["actorMovement"])
    {
        const YAML::Node limitNode = actorMovementNode.IsMap() ? actorMovementNode["levelRadiusLimit"] : YAML::Node();
        if (!limitNode || !limitNode.IsScalar())
        {
            errorMessage = "world.yml actorMovement must declare levelRadiusLimit";
            return false;
        }

        manifest.actorMovement.levelRadiusLimit = limitNode.as<float>();

        if (!std::isfinite(manifest.actorMovement.levelRadiusLimit) || manifest.actorMovement.levelRadiusLimit < 0.0f)
        {
            errorMessage = "world.yml actorMovement levelRadiusLimit must be a finite number, 0 or more";
            return false;
        }
    }

    if (const YAML::Node humNode = root["hum"])
    {
        const YAML::Node qbitsNode = humNode.IsMap() ? humNode["qbits"] : YAML::Node();
        const YAML::Node percentsNode = humNode.IsMap() ? humNode["percents"] : YAML::Node();

        if (!qbitsNode || !qbitsNode.IsSequence() || !percentsNode || !percentsNode.IsSequence()
            || percentsNode.size() != qbitsNode.size() + 1)
        {
            errorMessage = "world.yml hum needs qbits and one more percents than qbits";
            return false;
        }

        manifest.hum.declared = true;

        for (const YAML::Node &qbit : qbitsNode)
        {
            manifest.hum.qbits.push_back(qbit.as<uint32_t>());
        }

        for (const YAML::Node &percent : percentsNode)
        {
            manifest.hum.percents.push_back(percent.as<int>());
        }

        if (const YAML::Node mapsNode = humNode["maps"])
        {
            for (const auto &entry : mapsNode)
            {
                manifest.hum.mapPercents[toLowerCopy(entry.first.as<std::string>())] = entry.second.as<int>();
            }
        }

        for (const int percent : manifest.hum.percents)
        {
            if (percent < 0 || percent > 100)
            {
                errorMessage = "world.yml hum percents must be 0-100";
                return false;
            }
        }
    }

    if (const YAML::Node objectivesNode = root["objectives"])
    {
        if (!objectivesNode.IsSequence())
        {
            errorMessage = "world.yml objectives must be a list of QBits";
            return false;
        }

        for (const YAML::Node &qbit : objectivesNode)
        {
            manifest.objectiveQBits.push_back(qbit.as<uint32_t>());
        }
    }

    if (const YAML::Node burnNode = root["floorBurn"])
    {
        if (!burnNode.IsMap())
        {
            errorMessage = "world.yml floorBurn must be a map of type, resisted and maps";
            return false;
        }

        manifest.floorBurn.type = burnNode["type"].as<std::string>(manifest.floorBurn.type);
        manifest.floorBurn.resisted = burnNode["resisted"].as<bool>(false);

        if (const YAML::Node mapsNode = burnNode["maps"])
        {
            for (const auto &entry : mapsNode)
            {
                manifest.floorBurn.mapTypes[toLowerCopy(entry.first.as<std::string>())] = entry.second.as<std::string>();
            }
        }
    }

    if (const YAML::Node loadingNode = root["loadingScreens"])
    {
        if (!loadingNode.IsSequence() || loadingNode.size() == 0)
        {
            errorMessage = "world.yml loadingScreens must be a nonempty list of page names";
            return false;
        }

        for (const YAML::Node &page : loadingNode)
        {
            manifest.loadingScreens.push_back(page.as<std::string>());
        }
    }

    if (const YAML::Node completionNode = root["completion"])
    {
        WorldCompletionDefinition &completion = manifest.completion;

        if (!completionNode.IsMap() || completionNode["qbit"].as<uint32_t>(0) == 0
            || completionNode["art"].as<std::string>("").empty() || completionNode["headline"].as<std::string>("").empty())
        {
            errorMessage = "world.yml completion must declare a qbit, art and a headline";
            return false;
        }

        completion.declared = true;
        completion.qbit = completionNode["qbit"].as<uint32_t>();
        completion.continent = completionNode["continent"].as<std::string>("");
        completion.art = completionNode["art"].as<std::string>();
        completion.headline = completionNode["headline"].as<std::string>();
        completion.text = completionNode["text"].as<std::string>("");

        if (const YAML::Node layoutNode = completionNode["layout"])
        {
            const YAML::Node textNode = layoutNode["text"];
            const YAML::Node markNode = layoutNode["mark"];

            if (!textNode.IsSequence() || textNode.size() != 4 || !markNode.IsSequence() || markNode.size() != 3)
            {
                errorMessage = "world.yml completion layout must give text [left, top, right, bottom] and mark [x, y, "
                               "height]";
                return false;
            }

            completion.layout.declared = true;

            for (size_t index = 0; index < 4; ++index)
            {
                completion.layout.text[index] = textNode[index].as<float>();
            }

            for (size_t index = 0; index < 3; ++index)
            {
                completion.layout.mark[index] = markNode[index].as<float>();
            }
        }

        if (const YAML::Node variantsNode = completionNode["variants"])
        {
            for (const YAML::Node &variantNode : variantsNode)
            {
                WorldCompletionDefinition::Variant variant;
                variant.qbit = variantNode["qbit"].as<uint32_t>(0);
                variant.headline = variantNode["headline"].as<std::string>(completion.headline);
                variant.text = variantNode["text"].as<std::string>(completion.text);

                if (variant.qbit == 0)
                {
                    errorMessage = "world.yml completion variants must each declare a qbit";
                    return false;
                }

                completion.variants.push_back(std::move(variant));
            }
        }
    }

    if (const YAML::Node ambienceNode = root["ambience"])
    {
        if (!ambienceNode.IsMap())
        {
            errorMessage = "world.yml ambience must map map files to sound names";
            return false;
        }

        for (const auto &entry : ambienceNode)
        {
            manifest.ambience[toLowerCopy(entry.first.as<std::string>())] = entry.second.as<std::string>();
        }

        manifest.ambienceVolume = root["ambienceVolume"].as<float>(0.6f);
    }

    if (const YAML::Node areasNode = root["musicAreas"])
    {
        for (const auto &mapEntry : areasNode)
        {
            std::vector<WorldManifest::MusicArea> &areas =
                manifest.musicAreas[toLowerCopy(mapEntry.first.as<std::string>())];

            for (const YAML::Node &areaNode : mapEntry.second)
            {
                const std::vector<float> rect = areaNode["rect"].as<std::vector<float>>();

                if (rect.size() != 4 || rect[0] >= rect[2] || rect[1] >= rect[3] || areaNode["track"].as<int>(0) <= 0)
                {
                    errorMessage = "world.yml musicAreas entries need a track and rect [minX, minY, maxX, maxY]";
                    return false;
                }

                areas.push_back({areaNode["track"].as<int>(), {rect[0], rect[1], rect[2], rect[3]}});
            }
        }
    }

    if (const YAML::Node hirelingsNode = root["tavernHirelings"])
    {
        if (!hirelingsNode.IsScalar())
        {
            errorMessage = "world.yml tavernHirelings must be true or false";
            return false;
        }

        manifest.tavernHirelings = hirelingsNode.as<bool>();
    }

    const YAML::Node dependenciesNode = root["dependencies"];
    if (dependenciesNode)
    {
        if (!dependenciesNode.IsSequence())
        {
            errorMessage = "world.yml dependencies must be a sequence";
            return false;
        }

        std::unordered_set<std::string> dependencyIds;

        for (const YAML::Node &dependencyNode : dependenciesNode)
        {
            if (!dependencyNode.IsScalar())
            {
                errorMessage = "world.yml dependencies entries must be scalar package ids";
                return false;
            }

            const std::string dependencyId = normalizeWorldId(dependencyNode.as<std::string>());

            if (dependencyId.empty() || dependencyId == manifest.id || !dependencyIds.insert(dependencyId).second)
            {
                errorMessage = "world.yml dependencies contain an empty, self, or duplicate package id";
                return false;
            }

            manifest.dependencies.push_back(dependencyId);
        }
    }

    if (!parseContentIdRanges(root["idRanges"], "world.yml", manifest.idRanges, errorMessage))
    {
        return false;
    }

    const YAML::Node contributionsNode = root["tableContributions"];
    if (contributionsNode)
    {
        if (!contributionsNode.IsSequence())
        {
            errorMessage = "world.yml tableContributions must be a sequence";
            return false;
        }

        std::unordered_set<std::string> contributionKeys;

        for (const YAML::Node &contributionNode : contributionsNode)
        {
            if (!contributionNode.IsMap())
            {
                errorMessage = "world.yml tableContributions entries must be maps";
                return false;
            }

            TableContributionDefinition contribution = {};
            contribution.table = normalizedToken(scalarStringOrDefault(contributionNode, "table", {}));
            contribution.idDomain = normalizedToken(
                scalarStringOrDefault(contributionNode, "idDomain", contribution.table));
            contribution.path = scalarStringOrDefault(contributionNode, "path", {});
            contribution.sourceIdColumn = scalarUint32OrDefault(contributionNode, "sourceIdColumn", 0);
            contribution.canonicalIdColumn = scalarUint32OrDefault(contributionNode, "canonicalIdColumn", 0);
            const std::optional<TableContributionMode> mode =
                parseContributionMode(scalarStringOrDefault(contributionNode, "mode", {}));

            if (contribution.table.empty() || contribution.idDomain.empty() || !mode
                || !isSafePackageRelativePath(contribution.path))
            {
                errorMessage = "world.yml tableContributions contain an invalid table, mode, or relative path";
                return false;
            }

            contribution.mode = *mode;

            if (contribution.mode == TableContributionMode::Append
                && contribution.table == "items"
                && contribution.sourceIdColumn == contribution.canonicalIdColumn)
            {
                errorMessage = "world.yml item contribution requires distinct source and canonical id columns";
                return false;
            }

            const std::string contributionKey = contribution.table + "\n" + contribution.path;

            if (!contributionKeys.insert(contributionKey).second)
            {
                errorMessage = "world.yml tableContributions contain a duplicate table/path entry";
                return false;
            }

            if (contribution.mode == TableContributionMode::Append
                && manifest.findIdRange(contribution.idDomain) == nullptr)
            {
                errorMessage = "world.yml append contribution requires a declared id range for its table";
                return false;
            }

            manifest.tableContributions.push_back(std::move(contribution));
        }
    }

    manifest.loadedFromFile = true;
    return true;
}

}

const ContentIdRangeDefinition *WorldManifest::findIdRange(const std::string &domain) const
{
    const std::string normalizedDomain = normalizedToken(domain);

    for (const ContentIdRangeDefinition &range : idRanges)
    {
        if (range.domain == normalizedDomain)
        {
            return &range;
        }
    }

    return nullptr;
}

std::optional<WorldManifest> loadWorldManifest(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    const std::string &fallbackWorldId,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<std::string> manifestText = assetFileSystem.readTextFile(virtualPath);

    if (!manifestText)
    {
        errorMessage = "could not read " + virtualPath;
        return std::nullopt;
    }

    WorldManifest manifest = buildDefaultWorldManifest(fallbackWorldId);

    try
    {
        const YAML::Node root = YAML::Load(*manifestText);

        if (!parseManifestRoot(root, manifest, errorMessage))
        {
            return std::nullopt;
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = "could not parse " + virtualPath + ": " + exception.what();
        return std::nullopt;
    }

    return manifest;
}

bool loadMountedWorldManifests(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<WorldManifest> &manifests,
    std::string &errorMessage)
{
    manifests.clear();
    errorMessage.clear();

    for (const std::string &worldPackageId : assetFileSystem.enumerate("worlds"))
    {
        const std::string normalizedPackageId = normalizeWorldId(worldPackageId);

        if (normalizedPackageId.empty())
        {
            continue;
        }

        const std::string manifestPath = "worlds/" + normalizedPackageId + "/world.yml";
        std::string manifestError;
        const std::optional<WorldManifest> manifest =
            loadWorldManifest(assetFileSystem, manifestPath, normalizedPackageId, manifestError);

        if (!manifest)
        {
            if (assetFileSystem.exists(manifestPath))
            {
                errorMessage = "failed to load " + manifestPath + ": " + manifestError;
                return false;
            }

            continue;
        }

        if (manifest->id != normalizedPackageId)
        {
            errorMessage = "manifest id '" + manifest->id + "' does not match package path '"
                + normalizedPackageId + "'";
            return false;
        }

        manifests.push_back(*manifest);
    }

    std::sort(
        manifests.begin(),
        manifests.end(),
        [](const WorldManifest &left, const WorldManifest &right)
        {
            return left.id < right.id;
        });

    std::unordered_set<std::string> mountedPackageIds = {"engine"};

    for (const WorldManifest &manifest : manifests)
    {
        if (!mountedPackageIds.insert(manifest.id).second)
        {
            errorMessage = "duplicate mounted content package id: " + manifest.id;
            return false;
        }
    }

    for (const WorldManifest &manifest : manifests)
    {
        for (const std::string &dependency : manifest.dependencies)
        {
            if (!mountedPackageIds.contains(dependency))
            {
                errorMessage = "mounted content package '" + manifest.id + "' requires missing package '"
                    + dependency + "'";
                return false;
            }
        }
    }

    return true;
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
        parseManifestRoot(root, manifest, errorMessage);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse world.yml: ") + exception.what();
    }

    return manifest;
}


bool parseContentIdRanges(
    const YAML::Node &node,
    const std::string &owner,
    std::vector<ContentIdRangeDefinition> &ranges,
    std::string &errorMessage)
{
    if (!node)
    {
        return true;
    }

    if (!node.IsMap())
    {
        errorMessage = owner + " idRanges must be a map";
        return false;
    }

    std::unordered_set<std::string> domains;

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (!iterator->first.IsScalar() || !iterator->second.IsMap())
        {
            errorMessage = owner + " idRanges entries must map a domain to a range";
            return false;
        }

        ContentIdRangeDefinition range = {};
        range.domain = normalizedToken(iterator->first.as<std::string>());
        range.begin = scalarUint32OrDefault(iterator->second, "begin", 0);
        range.end = scalarUint32OrDefault(iterator->second, "end", 0);

        if (range.domain.empty() || range.begin == 0 || range.begin > range.end || !domains.insert(range.domain).second)
        {
            errorMessage = owner + " idRanges contain an invalid or duplicate domain range";
            return false;
        }

        ranges.push_back(std::move(range));
    }

    return true;
}

std::optional<std::string> overlappingContentIdRange(
    const std::vector<ContentIdRangeDefinition> &left,
    const std::vector<ContentIdRangeDefinition> &right)
{
    for (const ContentIdRangeDefinition &first : left)
    {
        for (const ContentIdRangeDefinition &second : right)
        {
            if (first.domain == second.domain && first.begin <= second.end && second.begin <= first.end)
            {
                return first.domain;
            }
        }
    }

    return std::nullopt;
}
}
