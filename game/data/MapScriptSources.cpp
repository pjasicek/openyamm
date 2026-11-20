#include "game/data/MapScriptSources.h"

#include "game/StringUtils.h"
#include "game/maps/MapIdentity.h"

namespace OpenYAMM::Game
{
std::optional<std::string> readFirstExistingText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath
)
{
    for (const std::string &candidate : candidates)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(candidate);

        if (text)
        {
            resolvedPath = candidate;
            return text;
        }
    }

    return std::nullopt;
}

std::optional<std::string> readExistingTexts(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath
)
{
    std::string combinedText;
    std::string combinedPath;

    for (const std::string &candidate : candidates)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(candidate);

        if (!text)
        {
            continue;
        }

        if (!combinedText.empty())
        {
            combinedText += "\n\n";
        }

        combinedText += *text;

        if (!combinedPath.empty())
        {
            combinedPath += "; ";
        }

        combinedPath += candidate;
    }

    if (combinedText.empty())
    {
        return std::nullopt;
    }

    resolvedPath = combinedPath;
    return combinedText;
}

std::string mapScriptBaseName(const std::string &fileName)
{
    const std::filesystem::path path(fileName);
    return path.stem().string();
}

std::vector<std::string> buildLuaScriptPathCandidates(const std::string &baseName, bool globalScope)
{
    if (globalScope)
    {
        return {
            "events/Global.lua",
            "events/global.lua",
        };
    }

    const std::string lowerBaseName = toLowerCopy(baseName);
    return {
        "events/maps/" + lowerBaseName + ".lua",
        "events/maps/" + baseName + ".lua",
    };
}

bool isLuaMapOverlayFileName(const std::string &entryName, const std::string &baseName)
{
    const std::string lowerEntryName = toLowerCopy(entryName);
    const std::string lowerBaseName = toLowerCopy(baseName);

    if (!lowerEntryName.ends_with(".lua"))
    {
        return false;
    }

    return lowerEntryName.starts_with(lowerBaseName + "_")
        || lowerEntryName == lowerBaseName + ".fixup.lua";
}

// Map overlays of the mounted packages, then those of the active ruleset's package (`rulesetRoot`, empty for
// Standard), which run last.
std::vector<std::string> buildLuaScriptOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName,
    const std::string &rulesetRoot)
{
    std::vector<std::string> directories = {"events/maps"};
    std::vector<std::string> candidates;

    if (!rulesetRoot.empty())
    {
        directories.push_back(rulesetRoot + "events/maps");
    }

    for (const std::string &directory : directories)
    {
        for (const std::string &entryName : assetFileSystem.enumerate(directory))
        {
            if (isLuaMapOverlayFileName(entryName, baseName))
            {
                candidates.push_back(directory + "/" + entryName);
            }
        }
    }

    return candidates;
}

// Global overlays of the mounted packages, then those of the active ruleset's package (`rulesetRoot`, empty for
// Standard), which run last.
std::vector<std::string> buildLuaGlobalScriptOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rulesetRoot)
{
    std::vector<std::string> directories = {"events"};
    std::vector<std::string> candidates;

    if (!rulesetRoot.empty())
    {
        directories.push_back(rulesetRoot + "events");
    }

    for (const std::string &directory : directories)
    {
        for (const std::string &entryName : assetFileSystem.enumerate(directory))
        {
            if (isLuaMapOverlayFileName(entryName, "Global"))
            {
                candidates.push_back(directory + "/" + entryName);
            }
        }
    }

    return candidates;
}

std::vector<std::filesystem::path> buildLuaScriptSidecarPathCandidates(
    const std::string &baseName,
    const std::optional<std::filesystem::path> &geometryPath,
    const std::optional<std::filesystem::path> &scenePath)
{
    const std::string lowerBaseName = toLowerCopy(baseName);
    std::vector<std::filesystem::path> candidates;

    const auto appendDirectoryCandidates =
        [&](const std::optional<std::filesystem::path> &directory)
    {
        if (!directory || directory->empty())
        {
            return;
        }

        const std::filesystem::path normalizedDirectory = directory->lexically_normal();
        const std::filesystem::path lowerCandidate = normalizedDirectory / (lowerBaseName + ".lua");
        candidates.push_back(lowerCandidate);

        const std::filesystem::path exactCandidate = normalizedDirectory / (baseName + ".lua");

        if (exactCandidate != lowerCandidate)
        {
            candidates.push_back(exactCandidate);
        }
    };

    appendDirectoryCandidates(geometryPath ? std::optional<std::filesystem::path>(geometryPath->parent_path()) : std::nullopt);
    appendDirectoryCandidates(scenePath ? std::optional<std::filesystem::path>(scenePath->parent_path()) : std::nullopt);
    appendDirectoryCandidates(std::filesystem::current_path());
    return candidates;
}

std::string appendLuaScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName,
    const std::string &rulesetRoot,
    const std::string &luaSource,
    std::string &resolvedPath)
{
    std::string combinedLuaSource = luaSource;

    for (const std::string &overlayPath : buildLuaScriptOverlayPathCandidates(assetFileSystem, baseName, rulesetRoot))
    {
        const std::optional<std::string> overlaySource = assetFileSystem.readTextFile(overlayPath);

        if (!overlaySource)
        {
            continue;
        }

        combinedLuaSource += "\n\n-- map overlay: " + overlayPath + "\n";
        combinedLuaSource += *overlaySource;
        resolvedPath += " + " + overlayPath;
    }

    return combinedLuaSource;
}

std::string appendLuaGlobalScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rulesetRoot,
    const std::string &luaSource,
    std::string &resolvedPath)
{
    std::string combinedLuaSource = luaSource;

    for (const std::string &overlayPath : buildLuaGlobalScriptOverlayPathCandidates(assetFileSystem, rulesetRoot))
    {
        const std::optional<std::string> overlaySource = assetFileSystem.readTextFile(overlayPath);

        if (!overlaySource)
        {
            continue;
        }

        combinedLuaSource += "\n\n-- global overlay: " + overlayPath + "\n";
        combinedLuaSource += *overlaySource;
        resolvedPath += " + " + overlayPath;
    }

    return combinedLuaSource;
}


std::vector<std::string> buildLuaSupportPathCandidates()
{
    return {
        "scripts/common/event_support.lua",
        "scripts/common/EventSupport.lua",
    };
}

std::vector<std::string> buildLuaWorldCommonPathCandidates(const std::string &worldId)
{
    std::vector<std::string> candidates = {
        "events/common/world_common.lua",
        "events/common/common.lua",
    };

    if (!worldId.empty())
    {
        const std::string normalizedWorldId = normalizeWorldId(worldId);
        candidates.push_back("events/common/" + normalizedWorldId + "_common.lua");
    }

    return candidates;
}

std::string prependLuaSupport(
    const std::optional<std::string> &supportSource,
    const std::optional<std::string> &worldCommonSource,
    const std::optional<std::string> &scriptSource)
{
    if (!scriptSource)
    {
        return {};
    }

    std::string combinedSource;

    if (supportSource && !supportSource->empty())
    {
        combinedSource += *supportSource;
        combinedSource += "\n\n";
    }

    if (worldCommonSource && !worldCommonSource->empty())
    {
        combinedSource += *worldCommonSource;
        combinedSource += "\n\n";
    }

    combinedSource += *scriptSource;
    return combinedSource;
}
}
