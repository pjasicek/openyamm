#include "game/maps/SceneOverlayPaths.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <functional>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
// The overlay files the rule picks: the world's (the merged maps folder) in name order, then the active ruleset's
// (`rulesetRoot`, empty for Standard) in name order.
std::vector<std::string> collectOverlayPaths(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::function<bool(const std::string &)> &isOverlay,
    const std::string &rulesetRoot)
{
    std::vector<std::string> candidates;
    const auto collect = [&](const std::string &directory)
    {
        std::vector<std::string> found;

        for (const std::string &entryName : assetFileSystem.enumerate(directory))
        {
            if (isOverlay(entryName))
            {
                found.push_back(directory + "/" + entryName);
            }
        }

        std::sort(found.begin(), found.end(), [](const std::string &left, const std::string &right)
        {
            return toLowerCopy(left) < toLowerCopy(right);
        });
        candidates.insert(candidates.end(), found.begin(), found.end());
    };

    collect("Data/games");

    if (!rulesetRoot.empty())
    {
        collect(rulesetRoot + "maps");
    }

    return candidates;
}
}

bool isSceneOverlayFileName(const std::string &entryName, const std::string &sceneFileName)
{
    const std::string lowerEntryName = toLowerCopy(entryName);
    const std::string lowerSceneFileName = toLowerCopy(sceneFileName);

    if (!lowerEntryName.ends_with(".yml") || lowerEntryName == lowerSceneFileName)
    {
        return false;
    }

    if (lowerEntryName.ends_with(".scene.yml"))
    {
        const std::string underscoreOverlayPrefix =
            lowerSceneFileName.substr(0, lowerSceneFileName.size() - 10) + "_";

        if (lowerEntryName.starts_with(underscoreOverlayPrefix))
        {
            return true;
        }
    }

    const std::string numberedOverlayPrefix = lowerSceneFileName.substr(0, lowerSceneFileName.size() - 4) + ".";
    return lowerEntryName.starts_with(numberedOverlayPrefix);
}

std::vector<std::string> buildSceneOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneFileName,
    const std::string &rulesetRoot)
{
    return collectOverlayPaths(
        assetFileSystem,
        [&sceneFileName](const std::string &entryName) { return isSceneOverlayFileName(entryName, sceneFileName); },
        rulesetRoot);
}

bool isCinematicsOverlayFileName(const std::string &entryName, const std::string &cinematicsFileName)
{
    constexpr std::string_view Suffix = ".cinematics.yml";
    const std::string lowerEntryName = toLowerCopy(entryName);
    const std::string lowerCinematicsFileName = toLowerCopy(cinematicsFileName);

    if (!lowerCinematicsFileName.ends_with(Suffix) || !lowerEntryName.ends_with(Suffix))
    {
        return false;
    }

    const std::string prefix = lowerCinematicsFileName.substr(0, lowerCinematicsFileName.size() - Suffix.size()) + "_";
    return lowerEntryName.size() > prefix.size() + Suffix.size() && lowerEntryName.starts_with(prefix);
}

std::vector<std::string> buildCinematicsOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &cinematicsFileName,
    const std::string &rulesetRoot)
{
    return collectOverlayPaths(
        assetFileSystem,
        [&cinematicsFileName](const std::string &entryName)
        {
            return isCinematicsOverlayFileName(entryName, cinematicsFileName);
        },
        rulesetRoot);
}
}
