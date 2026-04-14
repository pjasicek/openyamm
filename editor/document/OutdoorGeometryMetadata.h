#pragma once

#include <cstddef>
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct EditorMaterialTextureRemap
{
    std::string sourceMaterialName;
    std::string textureName;
};

struct EditorBModelImportSource
{
    std::string sourcePath;
    std::string sourceMeshName;
    float importScale = 1.0f;
    bool mergeCoplanarFaces = false;
    std::string defaultTextureName;
    std::vector<EditorMaterialTextureRemap> materialRemaps;
};

struct EditorBModelSourceTransform
{
    float originX = 0.0f;
    float originY = 0.0f;
    float originZ = 0.0f;
    std::array<float, 3> basisX = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> basisY = {0.0f, 1.0f, 0.0f};
    std::array<float, 3> basisZ = {0.0f, 0.0f, 1.0f};
};

struct EditorOutdoorGeometryMetadataEntry
{
    std::string geometryId;
    size_t runtimeBModelIndex = 0;
    EditorBModelImportSource importSource = {};
    std::optional<EditorBModelSourceTransform> sourceTransform = std::nullopt;
};

struct EditorOutdoorGeometryMetadata
{
    uint32_t version = 1;
    std::string mapFileName;
    std::vector<EditorOutdoorGeometryMetadataEntry> bmodels;
};

std::string serializeOutdoorGeometryMetadata(const EditorOutdoorGeometryMetadata &metadata);

std::optional<EditorOutdoorGeometryMetadata> loadOutdoorGeometryMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage);

void normalizeOutdoorGeometryMetadata(
    EditorOutdoorGeometryMetadata &metadata,
    const std::string &mapFileName,
    size_t bmodelCount);
}
