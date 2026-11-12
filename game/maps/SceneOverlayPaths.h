#pragma once

#include "engine/AssetFileSystem.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Which files beside a map's scene file are its overlays (`<stem>_<name>.scene.yml`, `<stem>.scene.<name>.yml`) and
// the order they apply in. In their own file, out of MapAssetLoader.cpp, so that tools which read a map with its
// overlays (the map studio) use the game's rule without the game's map loader.
bool isSceneOverlayFileName(const std::string &entryName, const std::string &sceneFileName);

// The world's overlays in name order, then the active ruleset's (`rulesetRoot`, empty for Standard).
std::vector<std::string> buildSceneOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneFileName,
    const std::string &rulesetRoot);
}
