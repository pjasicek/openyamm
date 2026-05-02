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
    bool initialize(
        const std::filesystem::path &basePath,
        const std::filesystem::path &assetRoot,
        AssetScaleTier assetScaleTier,
        const std::string &activeWorldId
    );
    bool switchActiveWorld(const std::string &activeWorldId);
    bool mountDevelopmentRoot(const std::filesystem::path &assetRoot);
    bool exists(const std::string &virtualPath) const;
    std::vector<std::string> enumerate(const std::string &virtualPath) const;
    std::optional<std::vector<uint8_t>> readBinaryFile(const std::string &virtualPath) const;
    std::optional<std::string> readTextFile(const std::string &virtualPath) const;
    std::optional<std::filesystem::path> resolvePhysicalPath(const std::string &virtualPath) const;
    std::vector<std::string> getSearchPaths() const;
    const std::filesystem::path &getDevelopmentRoot() const;
    const std::filesystem::path &getEditorDevelopmentRoot() const;
    const std::string &getActiveWorldId() const;
    AssetScaleTier getAssetScaleTier() const;
    void shutdown();

private:
    struct SearchMount
    {
        std::filesystem::path root;
        std::string mountPoint;
    };

    bool isInitialized() const;
    bool validateTierDirectories(const std::filesystem::path &assetRoot) const;
    bool mountDevelopmentPackageRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountSearchRoot(const std::filesystem::path &assetRoot, bool appendToPath);
    bool mountSearchRootAt(
        const std::filesystem::path &assetRoot,
        const std::string &mountPoint,
        bool appendToPath
    );
    bool validateMergedIconRoots(const std::filesystem::path &assetRoot) const;
    bool validateMergedAudioRoots(const std::filesystem::path &assetRoot) const;
    bool validateMergedPackageRoots(
        const std::filesystem::path &assetRoot,
        const char *pPackageDirectoryName,
        const char *pAssetTypeName
    ) const;
    bool mountMergedWorldIconRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldAudioRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldPackageRoots(
        const std::filesystem::path &assetRoot,
        const std::string &activeWorldId,
        const char *pPackageDirectoryName
    );
    std::string resolveVirtualPath(const std::string &virtualPath) const;
    std::vector<std::string> resolveVirtualPathCandidates(const std::string &virtualPath) const;
    static std::string normalizeVirtualPath(const std::string &virtualPath);
    static std::string normalizePackageId(const std::string &packageId, const std::string &defaultPackageId);
    static std::vector<std::string> expandPackageAliasCandidates(const std::string &virtualPath);
    static std::string remapTieredVirtualPath(const std::string &virtualPath, AssetScaleTier assetScaleTier);

    bool m_isInitialized;
    std::filesystem::path m_basePath;
    std::filesystem::path m_developmentRoot;
    std::filesystem::path m_editorDevelopmentRoot;
    std::string m_activeWorldId;
    AssetScaleTier m_assetScaleTier;
    std::vector<SearchMount> m_searchMounts;
};
}
