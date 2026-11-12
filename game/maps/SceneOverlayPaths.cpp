#include "game/maps/SceneOverlayPaths.h"

#include "game/StringUtils.h"

#include <algorithm>

namespace OpenYAMM::Game
{
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

// The world's overlays in name order, then the active ruleset's (`rulesetRoot`, empty for Standard).
std::vector<std::string> buildSceneOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneFileName,
    const std::string &rulesetRoot)
{
    std::vector<std::string> candidates;
    const auto collect = [&](const std::string &directory)
    {
        std::vector<std::string> found;

        for (const std::string &entryName : assetFileSystem.enumerate(directory))
        {
            if (isSceneOverlayFileName(entryName, sceneFileName))
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
