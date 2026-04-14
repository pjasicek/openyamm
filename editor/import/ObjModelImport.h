#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct ImportedModelPosition
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct ImportedModelFaceVertex
{
    size_t positionIndex = 0;
    bool hasUv = false;
    float u = 0.0f;
    float v = 0.0f;
};

struct ImportedModelFace
{
    std::vector<ImportedModelFaceVertex> vertices;
    std::string materialName;
};

struct ImportedModelMaterial
{
    std::string name;
    std::string textureLabel;
    std::string textureMimeType;
    std::vector<uint8_t> textureBytes;
};

struct ImportedModel
{
    std::string name;
    std::vector<ImportedModelPosition> positions;
    std::vector<ImportedModelFace> faces;
    std::vector<ImportedModelMaterial> materials;
};

using ImportedObjPosition = ImportedModelPosition;
using ImportedObjFaceVertex = ImportedModelFaceVertex;
using ImportedObjFace = ImportedModelFace;
using ImportedObjModel = ImportedModel;

bool loadImportedModelsFromFile(
    const std::filesystem::path &path,
    std::vector<ImportedModel> &models,
    std::string &errorMessage,
    bool mergeCoplanarFaces = false);

bool loadImportedModelFromFile(
    const std::filesystem::path &path,
    ImportedModel &model,
    std::string &errorMessage,
    const std::string &sourceMeshName = {},
    bool mergeCoplanarFaces = false);

bool loadObjModelFromFile(
    const std::filesystem::path &path,
    ImportedModel &model,
    std::string &errorMessage);
}
