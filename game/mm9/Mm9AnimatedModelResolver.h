#pragma once

#include "game/render/AnimatedModelAsset.h"

#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9AnimatedModelMaterialOverride
{
    size_t materialIndex = 0;
    std::string runtimeTexture;
};

struct Mm9AnimatedModelSkinBinding
{
    std::string id;
    std::vector<std::string> sourceSkins;
};

struct Mm9AnimatedModelRegistryEntry
{
    std::string modelId;
    std::vector<std::string> roles;
    std::string sourceModel;
    std::string modelAsset;
    std::string modelSidecar;
    std::vector<std::string> sourceSkins;
    std::vector<Mm9AnimatedModelSkinBinding> skinBindings;
};

struct Mm9AnimatedModelResolution
{
    std::string requestedSourceModel;
    std::string requestedSourceSkin;
    std::string normalizedSourceModel;
    std::vector<std::string> normalizedSourceSkins;
    std::string modelId;
    std::string skinBindingId;
    std::filesystem::path modelAssetPath;
    std::filesystem::path modelSidecarPath;
    std::vector<Mm9AnimatedModelMaterialOverride> materialOverrides;
};

class Mm9AnimatedModelResolver
{
public:
    bool loadRegistry(
        const std::filesystem::path &registryPath,
        std::string &errorMessage);

    std::optional<Mm9AnimatedModelResolution> resolve(
        const std::string &sourceModel,
        const std::string &sourceSkin,
        std::vector<AnimatedModelDiagnostic> &diagnostics) const;

    std::optional<Mm9AnimatedModelResolution> resolveModelAsset(
        const std::string &modelAsset,
        const std::string &skinBindingId,
        const std::string &sourceModel,
        const std::string &sourceSkin,
        std::vector<AnimatedModelDiagnostic> &diagnostics) const;

    const std::vector<Mm9AnimatedModelRegistryEntry> &entries() const;

private:
    std::filesystem::path m_worldRoot;
    std::vector<Mm9AnimatedModelRegistryEntry> m_entries;
    std::unordered_map<std::string, std::string> m_sourceModelAliases;
    std::unordered_map<std::string, std::string> m_sourceSkinAliases;
};

std::string normalizeMm9AnimatedModelSourceModelRef(const std::string &value);
std::vector<std::string> normalizeMm9AnimatedModelSourceSkinRefs(const std::string &value);
}
