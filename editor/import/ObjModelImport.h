#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct ImportedObjPosition
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct ImportedObjFaceVertex
{
    size_t positionIndex = 0;
    bool hasUv = false;
    float u = 0.0f;
    float v = 0.0f;
};

struct ImportedObjFace
{
    std::vector<ImportedObjFaceVertex> vertices;
    std::string materialName;
};

struct ImportedObjModel
{
    std::string name;
    std::vector<ImportedObjPosition> positions;
    std::vector<ImportedObjFace> faces;
};

bool loadObjModelFromFile(
    const std::filesystem::path &path,
    ImportedObjModel &model,
    std::string &errorMessage);
}
