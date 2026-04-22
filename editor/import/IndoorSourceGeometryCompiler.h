#pragma once

#include "editor/document/IndoorGeometryMetadata.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct IndoorSourceGeometryCompileResult
{
    Game::IndoorMapData indoorGeometry = {};
    std::vector<Game::IndoorSceneDoor> generatedDoors;
    std::vector<std::string> warnings;
};

bool compileIndoorSourceGeometry(
    const std::filesystem::path &sourcePath,
    const EditorIndoorGeometryMetadata &metadata,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage);
}
