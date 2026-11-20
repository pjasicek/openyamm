#pragma once

#include "engine/ApplicationConfig.h"

#include <filesystem>
#include <string>

namespace OpenYAMM::Game
{
// `--headless-export-indoor-bake-scene <map.blv> <output.json>`: what the indoor lighting bake
// (tools/lighting/bake_indoor.py) needs from a BLV, taken from the game's own loading so it matches what the game
// draws: every face's room, texture, flags and its vertices in their load pose (doors as the map starts), the static
// lights as the renderer lights with them (map lights and light-emitting decorations), and each sector's ambient.
int exportIndoorBakeScene(
    const Engine::ApplicationConfig &config,
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    const std::filesystem::path &outputPath);
}
