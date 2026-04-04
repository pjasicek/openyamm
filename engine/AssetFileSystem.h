#pragma once

#include "engine/AssetScaleTier.h"

#include <filesystem>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem
{
public:
    AssetFileSystem();
    ~AssetFileSystem();

    AssetFileSystem(const AssetFileSystem &) = delete;
    AssetFileSystem &operator=(const AssetFileSystem &) = delete;

    bool initialize(
        const std::filesystem::path &basePath,
        const std::filesystem::path &assetRoot,
        AssetScaleTier assetScaleTier
    );
    bool mountDevelopmentRoot(const std::filesystem::path &assetRoot);
    bool exists(const std::string &virtualPath) const;
    std::vector<std::string> enumerate(const std::string &virtualPath) const;
    std::optional<std::vector<uint8_t>> readBinaryFile(const std::string &virtualPath) const;
    std::optional<std::string> readTextFile(const std::string &virtualPath) const;
    std::vector<std::string> getSearchPaths() const;
    const std::filesystem::path &getDevelopmentRoot() const;
    AssetScaleTier getAssetScaleTier() const;
    void shutdown();

private:
    bool isInitialized() const;
    bool validateTierDirectories(const std::filesystem::path &assetRoot) const;
    std::string resolveVirtualPath(const std::string &virtualPath) const;
    static std::string normalizeVirtualPath(const std::string &virtualPath);
    static std::string remapTieredVirtualPath(const std::string &virtualPath, AssetScaleTier assetScaleTier);

    bool m_isInitialized;
    std::filesystem::path m_developmentRoot;
    AssetScaleTier m_assetScaleTier;
};
}
