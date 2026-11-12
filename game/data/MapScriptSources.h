#pragma once

#include "engine/AssetFileSystem.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Where a map's and the global event scripts are found and how their source is put together: the script itself, its
// overlays (`<base>_*.lua`, `<base>.fixup.lua`; the active ruleset's last), and the support and world-common scripts
// in front. In their own file, out of GameDataLoader.cpp, so that tools which read a map's events (the map studio's
// audits) use the game's rules without the game's data loader.
// The first of the candidates that exists, and all of them that exist joined in order (a world's common scripts).
std::optional<std::string> readFirstExistingText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath);

std::optional<std::string> readExistingTexts(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath);

std::string mapScriptBaseName(const std::string &fileName);

std::vector<std::string> buildLuaScriptPathCandidates(const std::string &baseName, bool globalScope);

bool isLuaMapOverlayFileName(const std::string &entryName, const std::string &baseName);

std::vector<std::string> buildLuaScriptOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName,
    const std::string &rulesetRoot);

std::vector<std::string> buildLuaGlobalScriptOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rulesetRoot);

std::vector<std::filesystem::path> buildLuaScriptSidecarPathCandidates(
    const std::string &baseName,
    const std::optional<std::filesystem::path> &geometryPath,
    const std::optional<std::filesystem::path> &scenePath);

std::string appendLuaScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName,
    const std::string &rulesetRoot,
    const std::string &luaSource,
    std::string &resolvedPath);

std::string appendLuaGlobalScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rulesetRoot,
    const std::string &luaSource,
    std::string &resolvedPath);

std::vector<std::string> buildLuaSupportPathCandidates();

std::vector<std::string> buildLuaWorldCommonPathCandidates(const std::string &worldId);

std::string prependLuaSupport(
    const std::optional<std::string> &supportSource,
    const std::optional<std::string> &worldCommonSource,
    const std::optional<std::string> &scriptSource);
}
