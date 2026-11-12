#pragma once

#include "engine/AssetPackIndex.h"
#include "engine/AssetScaleTier.h"

#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
struct AssetFileInfo
{
    uint64_t size = 0;
    int64_t modified = 0;
    bool archived = false;
};

class AssetReadStream
{
public:
    ~AssetReadStream();

    AssetReadStream(const AssetReadStream &) = delete;
    AssetReadStream &operator=(const AssetReadStream &) = delete;
    AssetReadStream(AssetReadStream &&) noexcept;
    AssetReadStream &operator=(AssetReadStream &&) noexcept;

    bool isOpen() const;
    int64_t read(void *pBuffer, size_t byteCount);
    bool seek(uint64_t absoluteOffset);
    int64_t tell() const;
    int64_t length() const;
    const std::string &virtualPath() const;

private:
    struct Impl;

    explicit AssetReadStream(std::unique_ptr<Impl> pImpl);

    std::unique_ptr<Impl> m_pImpl;

    friend class AssetFileSystem;
};

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
    bool initialize(
        const std::filesystem::path &basePath,
        const std::filesystem::path &assetRoot,
        AssetScaleTier assetScaleTier,
        const AssetScaleProfile &assetScaleProfile,
        const std::string &activeWorldId
    );
    // The installed content options apply only to a release's packs (assets/index.json), not to Android or
    // development roots.
    bool initialize(
        const std::filesystem::path &basePath,
        const std::filesystem::path &assetRoot,
        AssetScaleTier assetScaleTier,
        const AssetScaleProfile &assetScaleProfile,
        const std::string &activeWorldId,
        const InstalledContentOptions &installedContentOptions
    );
    bool switchActiveWorld(const std::string &activeWorldId);
    bool mountDevelopmentRoot(const std::filesystem::path &assetRoot);
    bool exists(const std::string &virtualPath) const;
    // Returns the selected virtual file path, including its actual scale directory, also inside archives.
    std::optional<std::string> resolveExistingFilePath(const std::string &virtualPath) const;
    std::optional<AssetFileInfo> fileInfo(const std::string &virtualPath) const;
    // Sorted entry names of a virtual directory over every mount and alias; kept until refreshLookupCache().
    std::vector<std::string> enumerate(const std::string &virtualPath) const;
    std::unique_ptr<AssetReadStream> openReadStream(const std::string &virtualPath) const;
    std::optional<std::vector<uint8_t>> readBinaryFile(const std::string &virtualPath) const;
    std::optional<std::string> readTextFile(const std::string &virtualPath) const;
    std::optional<std::filesystem::path> resolvePhysicalPath(const std::string &virtualPath) const;
    std::vector<std::string> getSearchPaths() const;
    const std::filesystem::path &getDevelopmentRoot() const;
    const std::filesystem::path &getEditorDevelopmentRoot() const;
    const std::string &getActiveWorldId() const;
    AssetScaleTier getAssetScaleTier() const;
    AssetScaleTier getAssetScaleTier(AssetScaleCategory assetScaleCategory) const;
    AssetScaleTier getAssetScaleTierForVirtualPath(const std::string &virtualPath) const;
    const AssetScaleProfile &getAssetScaleProfile() const;
    // A release's interface language has optional packs (fonts, sounds, videos) that are not downloaded yet: the game
    // shows English until the updater has them.
    bool languagePacksMissing() const;
    // The download size of a release language's optional packs not installed; 0 when installed or not a release.
    uint64_t missingLanguagePackBytes(const std::string &languageId) const;
    // Call after editing mounted files, with asset readers stopped. Mount changes invalidate automatically.
    void refreshLookupCache() const;
    uint64_t contentGeneration() const;
    void shutdown();

private:
    struct LookupCache;
    std::optional<std::string> findCaseInsensitiveVirtualPath(const std::string &virtualPath) const;
    struct SearchMount
    {
        std::filesystem::path root;
        std::string mountPoint;
        // The package root a content pack belongs to ("engine", "worlds/mm6"); the mount point otherwise.
        std::string packageMountPoint;
        bool archive = false;
        // A language's pack: in front of the packs whose files it replaces, but it does not decide which package an
        // unqualified request searches first (the active world's base packs do).
        bool languagePack = false;
    };

    bool isInitialized() const;
    bool validateTierDirectories(const std::filesystem::path &assetRoot) const;
    bool validateTierDirectoriesInMountedPackages() const;
    bool isPackagedAssetRoot(const std::filesystem::path &assetRoot) const;
    bool isAndroidApkAssetRoot(const std::filesystem::path &assetRoot) const;
    bool mountDevelopmentPackageRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountPackagedAssetRoot(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountAndroidApkAssetRoot(const std::string &activeWorldId);
    bool mountPackageArchiveIfPresent(const std::filesystem::path &archivePath, bool appendToPath);
    // The engine/ and worlds/<id>/ folders of mods/ in front of every pack; logs each file they bring.
    bool mountMods(const std::filesystem::path &modsRoot);
    // A development folder in front of a development asset root (InstalledContentOptions::extraMountRoot).
    bool mountExtraDevelopmentRoot(const std::filesystem::path &extraRoot);
    // The player's language packs at languages/, and the active pack's fonts, sounds, voices and videos in front of
    // the game's (devdocs/LOCALIZATION.md). A pack replaces nothing else.
    bool mountLanguagePack(bool packagedRoot);
    // Mounts the content packs of an index: the active world's in front, then the engine's and the other worlds'.
    bool mountContentPacks(
        const AssetPackIndex &index,
        const std::string &activeWorldId,
        const std::function<bool(const AssetPackRecord &, bool appendToPath)> &mountPack);
    bool mountSearchRoot(const std::filesystem::path &assetRoot, bool appendToPath);
    bool mountSearchRootAt(
        const std::filesystem::path &assetRoot,
        const std::string &mountPoint,
        bool appendToPath,
        const std::string &packageMountPoint = {},
        bool languagePack = false
    );
    void recordSearchMount(SearchMount searchMount, bool appendToPath);
    bool validateMergedIconRoots(const std::filesystem::path &assetRoot) const;
    bool validateMergedAudioRoots(const std::filesystem::path &assetRoot) const;
    bool validateMergedMusicRoots(const std::filesystem::path &assetRoot) const;
    bool validateMergedPackageRoots(
        const std::filesystem::path &assetRoot,
        const char *pPackageDirectoryName,
        const char *pAssetTypeName
    ) const;
    bool mountMergedWorldIconRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldAudioRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldMusicRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldVideoRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldMapRuntimeRoots(const std::filesystem::path &assetRoot, const std::string &activeWorldId);
    bool mountMergedWorldScaledPackageRoots(
        const std::filesystem::path &assetRoot,
        const std::string &activeWorldId,
        const char *pPackageDirectoryName,
        AssetScaleTier assetScaleTier
    );
    bool mountMergedWorldPackageRoots(
        const std::filesystem::path &assetRoot,
        const std::string &activeWorldId,
        const char *pPackageDirectoryName
    );
    bool loadIconPackagePolicy();
    std::string resolveVirtualPath(const std::string &virtualPath) const;
    std::vector<std::string> resolveVirtualPathCandidates(const std::string &virtualPath) const;
    static std::string normalizeVirtualPath(const std::string &virtualPath);
    static std::string normalizePackageId(const std::string &packageId, const std::string &defaultPackageId);
    static std::vector<std::string> expandPackageAliasCandidates(const std::string &virtualPath);
    static AssetScaleCategory assetScaleCategoryForVirtualPath(const std::string &virtualPath);
    static std::string baseTieredVirtualPath(const std::string &virtualPath);
    static std::string remapTieredVirtualPath(
        const std::string &virtualPath,
        const AssetScaleProfile &assetScaleProfile
    );

    bool m_isInitialized;
    std::filesystem::path m_basePath;
    std::filesystem::path m_developmentRoot;
    std::filesystem::path m_editorDevelopmentRoot;
    std::string m_activeWorldId;
    AssetScaleTier m_assetScaleTier;
    AssetScaleProfile m_assetScaleProfile;
    InstalledContentOptions m_installedContentOptions;
    // Package-owned icon roots override user scale preferences after a content migration.
    std::vector<std::pair<std::string, AssetScaleTier>> m_iconPackages;
    std::vector<SearchMount> m_searchMounts;
    bool m_androidApkAssetRoot;
    bool m_languagePacksMissing = false;
    std::vector<std::pair<std::string, uint64_t>> m_missingLanguageBytes;
    std::unique_ptr<LookupCache> m_pLookupCache;
    mutable uint64_t m_contentGeneration = 0;
};
}
