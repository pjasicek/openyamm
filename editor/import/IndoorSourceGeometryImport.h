#pragma once

#include "editor/document/IndoorGeometryMetadata.h"

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct IndoorSourceGeometryImportResult
{
    EditorIndoorGeometryMetadata metadata = {};
    size_t importedMeshCount = 0;
    size_t unclassifiedMeshCount = 0;
    std::vector<std::string> warnings;
};

bool importIndoorSourceGeometryMetadataFromModel(
    const std::filesystem::path &sourcePath,
    const std::string &mapFileName,
    IndoorSourceGeometryImportResult &result,
    std::string &errorMessage);
}
