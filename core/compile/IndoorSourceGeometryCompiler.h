#pragma once

#include "core/compile/IndoorGeometryMetadata.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct IndoorSourceFaceGroup
{
    std::string sourceNodeName;
    std::vector<uint16_t> faceIds;
};

struct IndoorSourceGeometryCompileResult
{
    Game::IndoorMapData indoorGeometry = {};
    std::vector<Game::IndoorSceneDoor> generatedDoors;
    std::vector<IndoorSourceFaceGroup> generatedFaceGroups;
    std::vector<std::string> warnings;
};

bool compileIndoorSourceGeometry(
    const std::filesystem::path &sourcePath,
    const EditorIndoorGeometryMetadata &metadata,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage);
}
