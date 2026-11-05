#pragma once

#include "engine/models/ModelAsset.h"

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

// The length of each animation clip of a glTF model by clip name, read from the file's JSON alone (the bounds glTF
// requires on every animation input accessor), without loading the model: a cheap look at a model's clips for
// gameplay that must not depend on loaded or posed models. Empty when the file cannot be read or parsed.
std::optional<std::unordered_map<std::string, float>> readGltfClipDurations(
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
