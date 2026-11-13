#pragma once

#include "engine/models/ModelAsset.h"

#include <array>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;

struct ModelLoadResult
{
    std::shared_ptr<const ModelAsset> asset;
    std::string error;
    std::vector<std::string> warnings;

    explicit operator bool() const
    {
        return asset != nullptr;
    }
};

// What gameplay reads of a glTF model without loading it, so it runs the same with models drawn or not: from the
// file's JSON alone (and 64 bytes of its BIN chunk), cheap enough to read once per monster kind.
struct GltfModelSummary
{
    // The length of each animation clip by clip name (the bounds glTF requires on every animation input accessor).
    std::unordered_map<std::string, float> clipDurations;
    // The lowest and highest point (+Y, model units) of its meshes in their bind pose: the bounds glTF requires on
    // every POSITION accessor, placed by their nodes or, for a skinned mesh, by its first joint's inverse bind matrix.
    // Empty without a bounded mesh.
    std::optional<std::array<float, 2>> bindPoseHeightRange;
};

// Empty when the file cannot be read or parsed.
std::optional<GltfModelSummary> readGltfModelSummary(
    const AssetFileSystem &assetFileSystem, const std::string &virtualPath);

class GltfModelLoader
{
public:
    ModelLoadResult load(const AssetFileSystem &assetFileSystem, const std::string &virtualPath) const;
};

class ModelAssetCache
{
public:
    ModelLoadResult load(const AssetFileSystem &assetFileSystem, const std::string &virtualPath);
    void clear();
    size_t size() const;

private:
    GltfModelLoader m_loader;
    std::unordered_map<std::string, std::shared_ptr<const ModelAsset>> m_assets;
};
}
