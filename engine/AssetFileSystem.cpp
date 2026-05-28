#include "engine/AssetFileSystem.h"

#include <physfs.h>
#if defined(__ANDROID__)
#include <SDL3/SDL_system.h>
#endif

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
constexpr const char *EditorDevelopmentRootName = "assets_editor_dev";
constexpr const char *EngineDevelopmentRootName = "engine";
constexpr const char *WorldsDevelopmentRootName = "worlds";
constexpr const char *DefaultActiveWorldId = "mm8";
constexpr const char *IconsDirectoryName = "icons";
constexpr const char *AudioDirectoryName = "audio";
constexpr const char *MusicDirectoryName = "music";
constexpr const char *VideosDirectoryName = "videos";
constexpr const char *MapsDirectoryName = "maps";
constexpr const char *EventsDirectoryName = "events";
constexpr const char *TexturesDirectoryName = "textures";
constexpr const char *TerrainDirectoryName = "terrain";
constexpr const char *SpritesDirectoryName = "sprites";
constexpr const char *TerrainTextureFallbackDirectoryName = "terrain_textures";
constexpr const char *SkyTextureDirectoryName = "sky_textures";
constexpr const char *LegacyDirectoryName = "_legacy";
constexpr const char *SingleAssetPackageName = "assets.zip";
constexpr const char *EngineAssetPackageName = "engine.zip";
constexpr std::array<const char *, 5> KnownWorldPackageIds = {"mm6", "mm7", "mm8", "mm9", "mmmerge"};

struct TieredAssetDirectory
{
    const char *pCanonicalDirectory;
    AssetScaleCategory category;
};

constexpr std::array<TieredAssetDirectory, 13> TieredAssetDirectories = {
    TieredAssetDirectory{"Data/bitmaps", AssetScaleCategory::Textures},
    TieredAssetDirectory{"Data/terrain", AssetScaleCategory::Terrain},
    TieredAssetDirectory{"Data/sprites", AssetScaleCategory::Sprites},
    TieredAssetDirectory{"Data/icons", AssetScaleCategory::Icons},
    TieredAssetDirectory{"Data/ui", AssetScaleCategory::Ui},
    TieredAssetDirectory{"bitmaps", AssetScaleCategory::Textures},
    TieredAssetDirectory{"textures", AssetScaleCategory::Textures},
    TieredAssetDirectory{"terrain", AssetScaleCategory::Terrain},
    TieredAssetDirectory{"sprites", AssetScaleCategory::Sprites},
    TieredAssetDirectory{"icons", AssetScaleCategory::Icons},
    TieredAssetDirectory{"ui", AssetScaleCategory::Ui},
    TieredAssetDirectory{"effects", AssetScaleCategory::Effects},
    TieredAssetDirectory{"fonts", AssetScaleCategory::Fonts}
};

struct VirtualPathAlias
{
    const char *pLegacyPrefix;
    const char *pPackagePrefix;
};

struct MergedRootFile
{
    std::string rootKey;
    std::filesystem::path filePath;
};

constexpr std::array<VirtualPathAlias, 34> PackagePathAliases = {
    VirtualPathAlias{"engine/audio", "audio"},
    VirtualPathAlias{"engine/data_tables/english", "data_tables/english"},
    VirtualPathAlias{"engine/data_tables", "data_tables"},
    VirtualPathAlias{"engine/events", "events"},
    VirtualPathAlias{"engine/fonts/english_text", "fonts/english_text"},
    VirtualPathAlias{"engine/fonts/icons", "fonts/icons"},
    VirtualPathAlias{"engine/fonts", "fonts"},
    VirtualPathAlias{"engine/icons", "icons"},
    VirtualPathAlias{"engine/music", "music"},
    VirtualPathAlias{"engine/rendering", "rendering"},
    VirtualPathAlias{"engine/scripts", "scripts"},
    VirtualPathAlias{"engine/sprites", "sprites"},
    VirtualPathAlias{"engine/terrain", "terrain"},
    VirtualPathAlias{"engine/textures", "textures"},
    VirtualPathAlias{"Data/data_tables/english", "data_tables/english"},
    VirtualPathAlias{"Data/data_tables", "data_tables"},
    VirtualPathAlias{"Data/games", "maps"},
    VirtualPathAlias{"Data/scripts/common", "scripts/common"},
    VirtualPathAlias{"Data/scripts/maps", "events/maps"},
    VirtualPathAlias{"Data/scripts", "events"},
    VirtualPathAlias{"Data/ui", "ui"},
    VirtualPathAlias{"Data/rendering", "rendering"},
    VirtualPathAlias{"Data/EnglishD", "audio"},
    VirtualPathAlias{"Data/EnglishT", "data_tables/english"},
    VirtualPathAlias{"Data/EnglishT", "fonts/english_text"},
    VirtualPathAlias{"Data/icons", "icons"},
    VirtualPathAlias{"Data/icons", "fonts/icons"},
    VirtualPathAlias{"Data/bitmaps", "textures"},
    VirtualPathAlias{"Data/bitmaps", "effects"},
    VirtualPathAlias{"Data/terrain", "terrain"},
    VirtualPathAlias{"Data/sprites", "sprites"},
    VirtualPathAlias{"Data/sprites", "effects"},
    VirtualPathAlias{"Videos", "videos"},
    VirtualPathAlias{"Anims/mightdod", "videos/legacy"}
};

constexpr std::array<VirtualPathAlias, 2> RootPathAliases = {
    VirtualPathAlias{"Music", "music"},
    VirtualPathAlias{"_legacy", "_legacy"}
};

std::filesystem::path deriveEditorDevelopmentRoot(const std::filesystem::path &assetRoot)
{
    if (assetRoot.filename() == EditorDevelopmentRootName)
    {
        return assetRoot;
    }

    return assetRoot.parent_path() / EditorDevelopmentRootName;
}

std::string toLowerAscii(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
}

bool filesHaveSameContents(const std::filesystem::path &left, const std::filesystem::path &right)
{
    std::error_code leftSizeError;
    const uintmax_t leftSize = std::filesystem::file_size(left, leftSizeError);

    std::error_code rightSizeError;
    const uintmax_t rightSize = std::filesystem::file_size(right, rightSizeError);

    if (leftSizeError || rightSizeError || leftSize != rightSize)
    {
        return false;
    }

    std::ifstream leftStream(left, std::ios::binary);
    std::ifstream rightStream(right, std::ios::binary);

    if (!leftStream.good() || !rightStream.good())
    {
        return false;
    }

    constexpr size_t BufferSize = 16384;
    std::array<char, BufferSize> leftBuffer = {};
    std::array<char, BufferSize> rightBuffer = {};

    while (leftStream.good() || rightStream.good())
    {
        leftStream.read(leftBuffer.data(), static_cast<std::streamsize>(leftBuffer.size()));
        rightStream.read(rightBuffer.data(), static_cast<std::streamsize>(rightBuffer.size()));

        const std::streamsize leftCount = leftStream.gcount();
        const std::streamsize rightCount = rightStream.gcount();

        if (leftCount != rightCount)
        {
            return false;
        }

        if (!std::equal(leftBuffer.begin(), leftBuffer.begin() + leftCount, rightBuffer.begin()))
        {
            return false;
        }
    }

    return true;
}

std::string canonicalPathKey(const std::filesystem::path &path)
{
    std::error_code canonicalError;
    const std::filesystem::path canonicalPath = std::filesystem::weakly_canonical(path, canonicalError);
    return (canonicalError ? path.lexically_normal() : canonicalPath).generic_string();
}

std::vector<std::filesystem::path> collectExistingWorldPackageRoots(
    const std::filesystem::path &assetRoot,
    const char *pPackageDirectoryName)
{
    std::vector<std::filesystem::path> packageRoots;
    const std::filesystem::path worldsRoot = assetRoot / WorldsDevelopmentRootName;

    if (!std::filesystem::exists(worldsRoot))
    {
        return packageRoots;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(worldsRoot))
    {
        if (!entry.is_directory())
        {
            continue;
        }

        const std::filesystem::path packageRoot = entry.path() / pPackageDirectoryName;

        if (std::filesystem::is_directory(packageRoot))
        {
            packageRoots.push_back(packageRoot);
        }
    }

    std::sort(
        packageRoots.begin(),
        packageRoots.end(),
        [](const std::filesystem::path &left, const std::filesystem::path &right)
        {
            return left.generic_string() < right.generic_string();
        });

    return packageRoots;
}

bool anyWorldPackageRootExists(const std::filesystem::path &assetRoot, const std::string &packageDirectoryName)
{
    const std::filesystem::path worldsRoot = assetRoot / WorldsDevelopmentRootName;

    if (!std::filesystem::exists(worldsRoot))
    {
        return false;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(worldsRoot))
    {
        if (entry.is_directory() && std::filesystem::is_directory(entry.path() / packageDirectoryName))
        {
            return true;
        }
    }

    return false;
}

bool packageDirectoryExistsForTier(
    const std::filesystem::path &assetRoot,
    const std::string &packageDirectoryName,
    AssetScaleTier assetScaleTier)
{
    if (assetScaleTier == AssetScaleTier::X1)
    {
        return true;
    }

    const std::string scaledDirectoryName = packageDirectoryName + assetScaleTierDirectorySuffix(assetScaleTier);

    return std::filesystem::is_directory(assetRoot / scaledDirectoryName)
        || std::filesystem::is_directory(assetRoot / EngineDevelopmentRootName / scaledDirectoryName)
        || anyWorldPackageRootExists(assetRoot, scaledDirectoryName);
}

bool isZipArchivePath(const std::filesystem::path &path)
{
    return std::filesystem::is_regular_file(path) && toLowerAscii(path.extension().string()) == ".zip";
}

std::vector<std::filesystem::path> collectExistingWorldPackageArchives(
    const std::filesystem::path &assetRoot)
{
    std::vector<std::filesystem::path> packageArchives;
    const std::filesystem::path worldsRoot = assetRoot / WorldsDevelopmentRootName;

    if (!std::filesystem::is_directory(worldsRoot))
    {
        return packageArchives;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(worldsRoot))
    {
        if (isZipArchivePath(entry.path()))
        {
            packageArchives.push_back(entry.path());
        }
    }

    std::sort(
        packageArchives.begin(),
        packageArchives.end(),
        [](const std::filesystem::path &left, const std::filesystem::path &right)
        {
            return left.generic_string() < right.generic_string();
        });

    return packageArchives;
}

bool legacyDirectoryExistsForTier(
    const std::filesystem::path &assetRoot,
    const std::string &legacyDirectoryName,
    AssetScaleTier assetScaleTier)
{
    if (assetScaleTier == AssetScaleTier::X1)
    {
        return true;
    }

    const std::filesystem::path legacyPath(legacyDirectoryName);
    const std::filesystem::path parentPath = legacyPath.parent_path();
    const std::string scaledDirectoryName =
        legacyPath.filename().string() + assetScaleTierDirectorySuffix(assetScaleTier);
    const std::filesystem::path scaledLegacyPath =
        parentPath.empty() ? std::filesystem::path(scaledDirectoryName) : parentPath / scaledDirectoryName;

    return std::filesystem::is_directory(assetRoot / scaledLegacyPath);
}

struct PhysicsFsListDeleter
{
    void operator()(char **pList) const
    {
        if (pList != nullptr)
        {
            PHYSFS_freeList(pList);
        }
    }
};

std::optional<std::string> findCaseInsensitiveVirtualPath(const std::string &virtualPath)
{
    const std::filesystem::path path(virtualPath);
    const std::string parentPath = path.parent_path().generic_string();
    const std::string requestedFileName = toLowerAscii(path.filename().string());

    if (requestedFileName.empty())
    {
        return std::nullopt;
    }

    const std::string directoryPath = parentPath.empty() ? "." : parentPath;
    char **pEnumeratedEntries = PHYSFS_enumerateFiles(directoryPath.c_str());
    std::unique_ptr<char *, PhysicsFsListDeleter> pEntryList(pEnumeratedEntries);

    if (pEnumeratedEntries == nullptr)
    {
        return std::nullopt;
    }

    for (char **pEntry = pEnumeratedEntries; *pEntry != nullptr; ++pEntry)
    {
        if (toLowerAscii(*pEntry) != requestedFileName)
        {
            continue;
        }

        return parentPath.empty()
            ? std::string(*pEntry)
            : parentPath + "/" + *pEntry;
    }

    return std::nullopt;
}

PHYSFS_File *openReadExactOrCaseInsensitive(const std::string &virtualPath)
{
    PHYSFS_File *pFile = PHYSFS_openRead(virtualPath.c_str());

    if (pFile != nullptr)
    {
        return pFile;
    }

    const std::optional<std::string> resolvedPath = findCaseInsensitiveVirtualPath(virtualPath);

    if (!resolvedPath)
    {
        return nullptr;
    }

    return PHYSFS_openRead(resolvedPath->c_str());
}

bool initializePhysicsFs(const std::filesystem::path &basePath)
{
#if defined(__ANDROID__)
    PHYSFS_AndroidInit androidInit = {};
    androidInit.jnienv = SDL_GetAndroidJNIEnv();
    androidInit.context = SDL_GetAndroidActivity();

    if (androidInit.jnienv == nullptr || androidInit.context == nullptr)
    {
        std::cerr << "PHYSFS_init failed: Android JNI environment or activity is unavailable\n";
        return false;
    }

    return PHYSFS_init(reinterpret_cast<const char *>(&androidInit)) != 0;
#else
    return PHYSFS_init(basePath.string().c_str()) != 0;
#endif
}
}

AssetFileSystem::AssetFileSystem()
    : m_isInitialized(false)
    , m_activeWorldId(DefaultActiveWorldId)
    , m_assetScaleTier(AssetScaleTier::X1)
    , m_assetScaleProfile(createUniformAssetScaleProfile(AssetScaleTier::X1))
    , m_androidApkAssetRoot(false)
{
}

AssetFileSystem::~AssetFileSystem()
{
    shutdown();
}

bool AssetFileSystem::initialize(
    const std::filesystem::path &basePath,
    const std::filesystem::path &assetRoot,
    AssetScaleTier assetScaleTier)
{
    return initialize(basePath, assetRoot, assetScaleTier, DefaultActiveWorldId);
}

bool AssetFileSystem::initialize(
    const std::filesystem::path &basePath,
    const std::filesystem::path &assetRoot,
    AssetScaleTier assetScaleTier,
    const std::string &activeWorldId)
{
    return initialize(
        basePath,
        assetRoot,
        assetScaleTier,
        createUniformAssetScaleProfile(assetScaleTier),
        activeWorldId);
}

bool AssetFileSystem::initialize(
    const std::filesystem::path &basePath,
    const std::filesystem::path &assetRoot,
    AssetScaleTier assetScaleTier,
    const AssetScaleProfile &assetScaleProfile,
    const std::string &activeWorldId)
{
    shutdown();

    if (!initializePhysicsFs(basePath))
    {
        std::cerr << "PHYSFS_init failed: " << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    m_isInitialized = true;
    m_basePath = basePath;
    m_assetScaleTier = assetScaleTier;
    m_assetScaleProfile = assetScaleProfile;
    m_activeWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);

    const bool androidApkAssetRoot = isAndroidApkAssetRoot(assetRoot);
    const bool packagedAssetRoot = androidApkAssetRoot || isPackagedAssetRoot(assetRoot);

    if (!packagedAssetRoot && !validateTierDirectories(assetRoot))
    {
        shutdown();
        return false;
    }

    if (androidApkAssetRoot)
    {
        if (!mountAndroidApkAssetRoot(m_activeWorldId))
        {
            shutdown();
            return false;
        }

        if (!validateTierDirectoriesInMountedPackages())
        {
            shutdown();
            return false;
        }
    }
    else if (packagedAssetRoot)
    {
        if (!mountPackagedAssetRoot(assetRoot, m_activeWorldId))
        {
            shutdown();
            return false;
        }

        if (!validateTierDirectoriesInMountedPackages())
        {
            shutdown();
            return false;
        }
    }
    else
    {
        if (!mountSearchRoot(assetRoot, true))
        {
            shutdown();
            return false;
        }

        if (!mountDevelopmentPackageRoots(assetRoot, m_activeWorldId))
        {
            shutdown();
            return false;
        }
    }

    m_developmentRoot = assetRoot;
    m_editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);

    if (packagedAssetRoot)
    {
        return true;
    }

    const std::filesystem::path editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);
    std::error_code createDirectoriesError;
    std::filesystem::create_directories(editorDevelopmentRoot, createDirectoriesError);

    if (createDirectoriesError)
    {
        std::cerr << "Could not create editor development root " << editorDevelopmentRoot << ": "
                  << createDirectoriesError.message() << '\n';
        shutdown();
        return false;
    }

    const std::filesystem::path editorWorldRoot =
        editorDevelopmentRoot / WorldsDevelopmentRootName / m_activeWorldId;
    std::filesystem::create_directories(editorWorldRoot, createDirectoriesError);

    if (createDirectoriesError)
    {
        std::cerr << "Could not create editor world package root " << editorWorldRoot << ": "
                  << createDirectoriesError.message() << '\n';
        shutdown();
        return false;
    }

    m_editorDevelopmentRoot = editorDevelopmentRoot;

    return true;
}

bool AssetFileSystem::switchActiveWorld(const std::string &activeWorldId)
{
    if (!isInitialized())
    {
        return false;
    }

    const std::filesystem::path basePath = m_basePath;
    const std::filesystem::path assetRoot = m_developmentRoot;
    const AssetScaleTier assetScaleTier = m_assetScaleTier;
    const AssetScaleProfile assetScaleProfile = m_assetScaleProfile;

    return initialize(basePath, assetRoot, assetScaleTier, assetScaleProfile, activeWorldId);
}

bool AssetFileSystem::mountDevelopmentRoot(const std::filesystem::path &assetRoot)
{
    if (isAndroidApkAssetRoot(assetRoot))
    {
        if (!mountAndroidApkAssetRoot(DefaultActiveWorldId))
        {
            return false;
        }

        m_activeWorldId = DefaultActiveWorldId;
        m_developmentRoot = assetRoot;
        m_editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);
        return true;
    }

    if (isPackagedAssetRoot(assetRoot))
    {
        if (!mountPackagedAssetRoot(assetRoot, DefaultActiveWorldId))
        {
            return false;
        }

        m_activeWorldId = DefaultActiveWorldId;
        m_developmentRoot = assetRoot;
        m_editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);
        return true;
    }

    if (!mountSearchRoot(assetRoot, true))
    {
        return false;
    }

    m_activeWorldId = DefaultActiveWorldId;

    if (!mountDevelopmentPackageRoots(assetRoot, m_activeWorldId))
    {
        return false;
    }

    m_developmentRoot = assetRoot;
    m_editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);
    return true;
}

bool AssetFileSystem::mountDevelopmentPackageRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    const std::string normalizedWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);
    const std::filesystem::path engineRoot = assetRoot / EngineDevelopmentRootName;
    const std::filesystem::path activeWorldRoot = assetRoot / WorldsDevelopmentRootName / normalizedWorldId;

    if (std::filesystem::exists(engineRoot) && !mountSearchRoot(engineRoot, false))
    {
        return false;
    }

    if (std::filesystem::exists(activeWorldRoot) && !mountSearchRoot(activeWorldRoot, false))
    {
        return false;
    }

    if (!mountMergedWorldMapRuntimeRoots(assetRoot, normalizedWorldId))
    {
        return false;
    }

    if (!mountMergedWorldPackageRoots(assetRoot, normalizedWorldId, SpritesDirectoryName))
    {
        return false;
    }

    if (!validateMergedIconRoots(assetRoot))
    {
        return false;
    }

    if (!mountMergedWorldIconRoots(assetRoot, normalizedWorldId))
    {
        return false;
    }

    if (!validateMergedAudioRoots(assetRoot))
    {
        return false;
    }

    if (!mountMergedWorldAudioRoots(assetRoot, normalizedWorldId))
    {
        return false;
    }

    if (!validateMergedMusicRoots(assetRoot))
    {
        return false;
    }

    if (!mountMergedWorldMusicRoots(assetRoot, normalizedWorldId))
    {
        return false;
    }

    if (!mountMergedWorldVideoRoots(assetRoot, normalizedWorldId))
    {
        return false;
    }

    return true;
}

bool AssetFileSystem::isPackagedAssetRoot(const std::filesystem::path &assetRoot) const
{
    if (isZipArchivePath(assetRoot))
    {
        return true;
    }

    if (!std::filesystem::is_directory(assetRoot))
    {
        return false;
    }

    return isZipArchivePath(assetRoot / SingleAssetPackageName)
        || isZipArchivePath(assetRoot / EngineAssetPackageName)
        || !collectExistingWorldPackageArchives(assetRoot).empty();
}

bool AssetFileSystem::isAndroidApkAssetRoot(const std::filesystem::path &assetRoot) const
{
#if defined(__ANDROID__)
    return normalizeVirtualPath(assetRoot.generic_string()) == "assets"
        || assetRoot.filename() == "assets";
#else
    (void)assetRoot;
    return false;
#endif
}

bool AssetFileSystem::mountAndroidApkAssetRoot(const std::string &activeWorldId)
{
#if defined(__ANDROID__)
    if (!isInitialized())
    {
        return false;
    }

    const char *pApkPath = PHYSFS_getBaseDir();

    if (pApkPath == nullptr || pApkPath[0] == '\0')
    {
        std::cerr << "PHYSFS_getBaseDir returned no Android APK path\n";
        return false;
    }

    if (!std::filesystem::exists(pApkPath))
    {
        std::cerr << "Android APK path does not exist: " << pApkPath << '\n';
        return false;
    }

    if (!PHYSFS_mount(pApkPath, "/", 1))
    {
        std::cerr << "PHYSFS_mount failed for Android APK " << pApkPath << ": "
                  << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    SearchMount searchMount;
    searchMount.root = pApkPath;
    searchMount.mountPoint = "";
    searchMount.archive = true;
    m_searchMounts.push_back(searchMount);
    m_activeWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);
    m_androidApkAssetRoot = true;

    std::cout << "Mounted Android APK asset root: " << pApkPath << '\n';
    return true;
#else
    (void)activeWorldId;
    return false;
#endif
}

bool AssetFileSystem::mountPackagedAssetRoot(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    const std::string normalizedWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);

    if (isZipArchivePath(assetRoot))
    {
        return mountSearchRoot(assetRoot, true);
    }

    if (!std::filesystem::is_directory(assetRoot))
    {
        std::cerr << "Packaged asset root does not exist: " << assetRoot << '\n';
        return false;
    }

    if (!mountPackageArchiveIfPresent(assetRoot / SingleAssetPackageName, true))
    {
        return false;
    }

    if (!mountPackageArchiveIfPresent(assetRoot / EngineAssetPackageName, true))
    {
        return false;
    }

    const std::filesystem::path activeWorldArchive =
        assetRoot / WorldsDevelopmentRootName / (normalizedWorldId + ".zip");

    if (!mountPackageArchiveIfPresent(activeWorldArchive, false))
    {
        return false;
    }

    const std::vector<std::filesystem::path> worldArchives = collectExistingWorldPackageArchives(assetRoot);

    for (const std::filesystem::path &worldArchive : worldArchives)
    {
        if (worldArchive != activeWorldArchive && !mountPackageArchiveIfPresent(worldArchive, true))
        {
            return false;
        }
    }

    return true;
}

bool AssetFileSystem::mountPackageArchiveIfPresent(
    const std::filesystem::path &archivePath,
    bool appendToPath)
{
    if (!std::filesystem::exists(archivePath))
    {
        return true;
    }

    if (!isZipArchivePath(archivePath))
    {
        std::cerr << "Asset package is not a zip archive: " << archivePath << '\n';
        return false;
    }

    return mountSearchRoot(archivePath, appendToPath);
}

bool AssetFileSystem::mountSearchRoot(const std::filesystem::path &assetRoot, bool appendToPath)
{
    return mountSearchRootAt(assetRoot, "/", appendToPath);
}

bool AssetFileSystem::mountSearchRootAt(
    const std::filesystem::path &assetRoot,
    const std::string &mountPoint,
    bool appendToPath)
{
    if (!isInitialized())
    {
        return false;
    }

    if (!std::filesystem::exists(assetRoot))
    {
        std::cerr << "Asset root does not exist: " << assetRoot << '\n';
        return false;
    }

    if (!PHYSFS_mount(assetRoot.string().c_str(), mountPoint.c_str(), appendToPath ? 1 : 0))
    {
        std::cerr << "PHYSFS_mount failed for " << assetRoot << " at " << mountPoint << ": "
                  << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    SearchMount searchMount;
    searchMount.root = assetRoot;
    searchMount.mountPoint = normalizeVirtualPath(mountPoint);
    searchMount.archive = isZipArchivePath(assetRoot);

    if (appendToPath)
    {
        m_searchMounts.push_back(searchMount);
    }
    else
    {
        m_searchMounts.insert(m_searchMounts.begin(), searchMount);
    }

    return true;
}

bool AssetFileSystem::validateMergedPackageRoots(
    const std::filesystem::path &assetRoot,
    const char *pPackageDirectoryName,
    const char *pAssetTypeName) const
{
    std::unordered_map<std::string, MergedRootFile> knownPackageFiles;
    std::vector<std::filesystem::path> packageRoots;

    const std::filesystem::path enginePackageRoot =
        assetRoot / EngineDevelopmentRootName / pPackageDirectoryName;

    if (std::filesystem::is_directory(enginePackageRoot))
    {
        packageRoots.push_back(enginePackageRoot);
    }

    const std::vector<std::filesystem::path> worldPackageRoots =
        collectExistingWorldPackageRoots(assetRoot, pPackageDirectoryName);
    packageRoots.insert(packageRoots.end(), worldPackageRoots.begin(), worldPackageRoots.end());

    for (const std::filesystem::path &packageRoot : packageRoots)
    {
        const std::string rootKey = canonicalPathKey(packageRoot);

        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(packageRoot))
        {
            if (!entry.is_regular_file())
            {
                continue;
            }

            const std::string logicalName = toLowerAscii(entry.path().filename().string());
            const auto existingIterator = knownPackageFiles.find(logicalName);

            if (existingIterator == knownPackageFiles.end())
            {
                knownPackageFiles.emplace(logicalName, MergedRootFile{rootKey, entry.path()});
                continue;
            }

            const MergedRootFile &existingFile = existingIterator->second;

            if (existingFile.rootKey == rootKey)
            {
                continue;
            }

            if (!filesHaveSameContents(existingFile.filePath, entry.path()))
            {
                std::cerr << "Conflicting " << pAssetTypeName << " asset " << logicalName << " exists in both "
                          << existingFile.filePath << " and " << entry.path() << '\n';
                return false;
            }
        }
    }

    return true;
}

bool AssetFileSystem::validateMergedIconRoots(const std::filesystem::path &assetRoot) const
{
    return validateMergedPackageRoots(assetRoot, IconsDirectoryName, "icon");
}

bool AssetFileSystem::validateMergedAudioRoots(const std::filesystem::path &assetRoot) const
{
    return validateMergedPackageRoots(assetRoot, AudioDirectoryName, "audio");
}

bool AssetFileSystem::validateMergedMusicRoots(const std::filesystem::path &assetRoot) const
{
    return validateMergedPackageRoots(assetRoot, MusicDirectoryName, "music");
}

bool AssetFileSystem::mountMergedWorldPackageRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId,
    const char *pPackageDirectoryName)
{
    const std::string normalizedWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);
    const std::filesystem::path activeWorldPackageRoot =
        assetRoot / WorldsDevelopmentRootName / normalizedWorldId / pPackageDirectoryName;
    const std::filesystem::path enginePackageRoot =
        assetRoot / EngineDevelopmentRootName / pPackageDirectoryName;
    std::vector<std::filesystem::path> packageRoots;

    if (std::filesystem::is_directory(activeWorldPackageRoot))
    {
        packageRoots.push_back(activeWorldPackageRoot);
    }

    if (std::filesystem::is_directory(enginePackageRoot))
    {
        packageRoots.push_back(enginePackageRoot);
    }

    const std::vector<std::filesystem::path> worldPackageRoots =
        collectExistingWorldPackageRoots(assetRoot, pPackageDirectoryName);

    for (const std::filesystem::path &worldPackageRoot : worldPackageRoots)
    {
        if (worldPackageRoot != activeWorldPackageRoot)
        {
            packageRoots.push_back(worldPackageRoot);
        }
    }

    for (const std::filesystem::path &packageRoot : packageRoots)
    {
        if (!mountSearchRootAt(packageRoot, "/" + std::string(pPackageDirectoryName), true))
        {
            return false;
        }
    }

    return true;
}

bool AssetFileSystem::mountMergedWorldIconRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, IconsDirectoryName);
}

bool AssetFileSystem::mountMergedWorldAudioRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, AudioDirectoryName);
}

bool AssetFileSystem::mountMergedWorldMusicRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, MusicDirectoryName);
}

bool AssetFileSystem::mountMergedWorldVideoRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, VideosDirectoryName);
}

bool AssetFileSystem::mountMergedWorldMapRuntimeRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId)
{
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, MapsDirectoryName)
        && mountMergedWorldPackageRoots(assetRoot, activeWorldId, EventsDirectoryName)
        && mountMergedWorldPackageRoots(assetRoot, activeWorldId, TexturesDirectoryName)
        && mountMergedWorldPackageRoots(assetRoot, activeWorldId, TerrainDirectoryName)
        && mountMergedWorldScaledPackageRoots(
            assetRoot,
            activeWorldId,
            TexturesDirectoryName,
            assetScaleTierForCategory(m_assetScaleProfile, AssetScaleCategory::Textures))
        && mountMergedWorldScaledPackageRoots(
            assetRoot,
            activeWorldId,
            TerrainDirectoryName,
            assetScaleTierForCategory(m_assetScaleProfile, AssetScaleCategory::Terrain))
        && mountMergedWorldPackageRoots(assetRoot, activeWorldId, LegacyDirectoryName);
}

bool AssetFileSystem::mountMergedWorldScaledPackageRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId,
    const char *pPackageDirectoryName,
    AssetScaleTier assetScaleTier)
{
    if (assetScaleTier == AssetScaleTier::X1)
    {
        return true;
    }

    const std::string scaledPackageDirectoryName =
        std::string(pPackageDirectoryName) + assetScaleTierDirectorySuffix(assetScaleTier);
    return mountMergedWorldPackageRoots(assetRoot, activeWorldId, scaledPackageDirectoryName.c_str());
}

bool AssetFileSystem::exists(const std::string &virtualPath) const
{
    if (!isInitialized())
    {
        return false;
    }

    const std::vector<std::string> resolvedPaths = resolveVirtualPathCandidates(virtualPath);

    for (const std::string &resolvedPath : resolvedPaths)
    {
        if (PHYSFS_exists(resolvedPath.c_str()) != 0)
        {
            return true;
        }

        if (findCaseInsensitiveVirtualPath(resolvedPath))
        {
            return true;
        }
    }

    return false;
}

std::vector<std::string> AssetFileSystem::enumerate(const std::string &virtualPath) const
{
    std::vector<std::string> entries;
    std::unordered_set<std::string> knownEntries;

    if (!isInitialized())
    {
        return entries;
    }

    const std::vector<std::string> resolvedPaths = resolveVirtualPathCandidates(virtualPath);

    for (const std::string &resolvedPath : resolvedPaths)
    {
        char **pEnumeratedEntries = PHYSFS_enumerateFiles(resolvedPath.c_str());
        std::unique_ptr<char *, PhysicsFsListDeleter> pEntryList(pEnumeratedEntries);

        if (pEnumeratedEntries == nullptr)
        {
            continue;
        }

        for (char **pEntry = pEnumeratedEntries; *pEntry != nullptr; ++pEntry)
        {
            if (knownEntries.insert(*pEntry).second)
            {
                entries.emplace_back(*pEntry);
            }
        }
    }

    std::sort(entries.begin(), entries.end());
    return entries;
}

std::optional<std::string> AssetFileSystem::readTextFile(const std::string &virtualPath) const
{
    const std::optional<std::vector<uint8_t>> fileBytes = readBinaryFile(virtualPath);

    if (!fileBytes)
    {
        return std::nullopt;
    }

    return std::string(fileBytes->begin(), fileBytes->end());
}

std::optional<std::vector<uint8_t>> AssetFileSystem::readBinaryFile(const std::string &virtualPath) const
{
    if (!isInitialized())
    {
        return std::nullopt;
    }

    const std::vector<std::string> resolvedPaths = resolveVirtualPathCandidates(virtualPath);
    PHYSFS_File *pFile = nullptr;

    for (const std::string &resolvedPath : resolvedPaths)
    {
        pFile = openReadExactOrCaseInsensitive(resolvedPath);

        if (pFile != nullptr)
        {
            break;
        }
    }

    if (pFile == nullptr)
    {
        return std::nullopt;
    }

    const PHYSFS_sint64 fileLength = PHYSFS_fileLength(pFile);

    if (fileLength < 0)
    {
        PHYSFS_close(pFile);
        return std::nullopt;
    }

    std::vector<uint8_t> contents(static_cast<size_t>(fileLength));
    const PHYSFS_sint64 bytesRead = PHYSFS_readBytes(pFile, contents.data(), fileLength);
    PHYSFS_close(pFile);

    if (bytesRead != fileLength)
    {
        return std::nullopt;
    }

    return contents;
}

std::vector<std::string> AssetFileSystem::getSearchPaths() const
{
    std::vector<std::string> searchPaths;

    if (!isInitialized())
    {
        return searchPaths;
    }

    char **pRawSearchPaths = PHYSFS_getSearchPath();
    std::unique_ptr<char *, PhysicsFsListDeleter> pSearchPathList(pRawSearchPaths);

    if (pRawSearchPaths == nullptr)
    {
        return searchPaths;
    }

    for (char **pSearchPath = pRawSearchPaths; *pSearchPath != nullptr; ++pSearchPath)
    {
        searchPaths.emplace_back(*pSearchPath);
    }

    return searchPaths;
}

std::optional<std::filesystem::path> AssetFileSystem::resolvePhysicalPath(const std::string &virtualPath) const
{
    if (!isInitialized())
    {
        return std::nullopt;
    }

    const std::vector<std::string> resolvedPaths = resolveVirtualPathCandidates(virtualPath);

    for (const std::string &resolvedPath : resolvedPaths)
    {
        std::vector<std::string> physicalPathCandidates = {resolvedPath};

        const std::optional<std::string> caseInsensitivePath = findCaseInsensitiveVirtualPath(resolvedPath);

        if (caseInsensitivePath && *caseInsensitivePath != resolvedPath)
        {
            physicalPathCandidates.push_back(*caseInsensitivePath);
        }

        for (const SearchMount &searchMount : m_searchMounts)
        {
            if (searchMount.archive)
            {
                continue;
            }

            for (const std::string &physicalPathCandidate : physicalPathCandidates)
            {
                std::filesystem::path relativePath = physicalPathCandidate;

                if (!searchMount.mountPoint.empty())
                {
                    const std::string mountPointPrefix = searchMount.mountPoint + "/";

                    if (physicalPathCandidate == searchMount.mountPoint)
                    {
                        relativePath.clear();
                    }
                    else if (physicalPathCandidate.starts_with(mountPointPrefix))
                    {
                        relativePath = physicalPathCandidate.substr(mountPointPrefix.size());
                    }
                    else
                    {
                        continue;
                    }
                }

                const std::filesystem::path candidate =
                    searchMount.root / relativePath;

                if (std::filesystem::exists(candidate))
                {
                    std::error_code canonicalError;
                    const std::filesystem::path canonicalPath =
                        std::filesystem::weakly_canonical(candidate, canonicalError);
                    return canonicalError ? candidate.lexically_normal() : canonicalPath;
                }
            }
        }
    }

    return std::nullopt;
}

const std::filesystem::path &AssetFileSystem::getDevelopmentRoot() const
{
    return m_developmentRoot;
}

const std::filesystem::path &AssetFileSystem::getEditorDevelopmentRoot() const
{
    return m_editorDevelopmentRoot;
}

const std::string &AssetFileSystem::getActiveWorldId() const
{
    return m_activeWorldId;
}

AssetScaleTier AssetFileSystem::getAssetScaleTier() const
{
    return m_assetScaleTier;
}

AssetScaleTier AssetFileSystem::getAssetScaleTier(AssetScaleCategory assetScaleCategory) const
{
    return assetScaleTierForCategory(m_assetScaleProfile, assetScaleCategory);
}

AssetScaleTier AssetFileSystem::getAssetScaleTierForVirtualPath(const std::string &virtualPath) const
{
    return getAssetScaleTier(assetScaleCategoryForVirtualPath(normalizeVirtualPath(virtualPath)));
}

const AssetScaleProfile &AssetFileSystem::getAssetScaleProfile() const
{
    return m_assetScaleProfile;
}

void AssetFileSystem::shutdown()
{
    if (!isInitialized())
    {
        return;
    }

    PHYSFS_deinit();
    m_isInitialized = false;
    m_basePath.clear();
    m_developmentRoot.clear();
    m_editorDevelopmentRoot.clear();
    m_activeWorldId = DefaultActiveWorldId;
    m_assetScaleTier = AssetScaleTier::X1;
    m_assetScaleProfile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    m_searchMounts.clear();
    m_androidApkAssetRoot = false;
}

bool AssetFileSystem::isInitialized() const
{
    return m_isInitialized;
}

bool AssetFileSystem::validateTierDirectories(const std::filesystem::path &assetRoot) const
{
    struct RequiredTieredDirectory
    {
        AssetScaleCategory category;
        const char *pPackageDirectoryName;
        const char *pLegacyDirectoryName;
    };

    constexpr std::array<RequiredTieredDirectory, 4> RequiredTieredDirectories = {
        RequiredTieredDirectory{AssetScaleCategory::Textures, "textures", "Data/bitmaps"},
        RequiredTieredDirectory{AssetScaleCategory::Terrain, "terrain", "Data/terrain"},
        RequiredTieredDirectory{AssetScaleCategory::Sprites, "sprites", "Data/sprites"},
        RequiredTieredDirectory{AssetScaleCategory::Icons, "icons", "Data/icons"}
    };

    for (const RequiredTieredDirectory &requiredDirectory : RequiredTieredDirectories)
    {
        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(m_assetScaleProfile, requiredDirectory.category);

        if (assetScaleTier == AssetScaleTier::X1)
        {
            continue;
        }

        const bool packageDirectoryExists = packageDirectoryExistsForTier(
            assetRoot,
            requiredDirectory.pPackageDirectoryName,
            assetScaleTier);
        const bool legacyDirectoryExists = requiredDirectory.pLegacyDirectoryName[0] != '\0'
            && legacyDirectoryExistsForTier(assetRoot, requiredDirectory.pLegacyDirectoryName, assetScaleTier);
        if (!packageDirectoryExists && !legacyDirectoryExists)
        {
            std::cerr << "Selected " << requiredDirectory.pPackageDirectoryName << " asset tier "
                      << assetScaleTierToString(assetScaleTier)
                      << " is missing required directory under " << assetRoot << '\n';
            return false;
        }
    }

    return true;
}

bool AssetFileSystem::validateTierDirectoriesInMountedPackages() const
{
    struct RequiredTieredDirectory
    {
        AssetScaleCategory category;
        const char *pPackageDirectoryName;
        const char *pLegacyDirectoryName;
    };

    constexpr std::array<RequiredTieredDirectory, 4> RequiredTieredDirectories = {
        RequiredTieredDirectory{AssetScaleCategory::Textures, "textures", "Data/bitmaps"},
        RequiredTieredDirectory{AssetScaleCategory::Terrain, "terrain", "Data/terrain"},
        RequiredTieredDirectory{AssetScaleCategory::Sprites, "sprites", "Data/sprites"},
        RequiredTieredDirectory{AssetScaleCategory::Icons, "icons", "Data/icons"}
    };

    for (const RequiredTieredDirectory &requiredDirectory : RequiredTieredDirectories)
    {
        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(m_assetScaleProfile, requiredDirectory.category);

        if (assetScaleTier == AssetScaleTier::X1)
        {
            continue;
        }

        const std::string scaledPackageDirectoryName =
            std::string(requiredDirectory.pPackageDirectoryName) + assetScaleTierDirectorySuffix(assetScaleTier);
        const std::filesystem::path legacyPath(requiredDirectory.pLegacyDirectoryName);
        const std::filesystem::path parentPath = legacyPath.parent_path();
        const std::string scaledLegacyDirectoryName =
            legacyPath.filename().string() + assetScaleTierDirectorySuffix(assetScaleTier);
        const std::filesystem::path scaledLegacyPath = parentPath.empty()
            ? std::filesystem::path(scaledLegacyDirectoryName)
            : parentPath / scaledLegacyDirectoryName;

        if (exists(scaledPackageDirectoryName) || exists(scaledLegacyPath.generic_string()))
        {
            continue;
        }

        std::cerr << "Selected " << requiredDirectory.pPackageDirectoryName << " asset tier "
                  << assetScaleTierToString(assetScaleTier)
                  << " is missing required directory in mounted asset packages\n";
        return false;
    }

    return true;
}

std::string AssetFileSystem::resolveVirtualPath(const std::string &virtualPath) const
{
    const std::vector<std::string> candidates = resolveVirtualPathCandidates(virtualPath);
    return candidates.empty() ? std::string() : candidates.front();
}

std::vector<std::string> AssetFileSystem::resolveVirtualPathCandidates(const std::string &virtualPath) const
{
    std::vector<std::string> resolvedPaths;
    std::unordered_set<std::string> knownPaths;
    const std::string normalizedPath = normalizeVirtualPath(virtualPath);
    const std::vector<std::string> aliasCandidates = expandPackageAliasCandidates(normalizedPath);

    const auto appendCandidate = [&resolvedPaths, &knownPaths](const std::string &candidate)
    {
        if (knownPaths.insert(candidate).second)
        {
            resolvedPaths.push_back(candidate);
        }
    };

    const auto appendCandidateWithAndroidApkPrefixes =
        [this, &appendCandidate](const std::string &candidate)
    {
        appendCandidate(candidate);

        const std::vector<std::string> androidCandidates = expandAndroidApkAssetCandidates(candidate);

        for (const std::string &androidCandidate : androidCandidates)
        {
            appendCandidate(androidCandidate);
        }
    };

    for (const std::string &candidate : aliasCandidates)
    {
        const std::string remappedCandidate = remapTieredVirtualPath(candidate, m_assetScaleProfile);
        appendCandidateWithAndroidApkPrefixes(remappedCandidate);
        appendCandidateWithAndroidApkPrefixes(baseTieredVirtualPath(candidate));
    }

    const std::string remappedLegacyPath = remapTieredVirtualPath(normalizedPath, m_assetScaleProfile);
    appendCandidateWithAndroidApkPrefixes(remappedLegacyPath);
    appendCandidateWithAndroidApkPrefixes(baseTieredVirtualPath(normalizedPath));

    return resolvedPaths;
}

std::vector<std::string> AssetFileSystem::expandAndroidApkAssetCandidates(const std::string &virtualPath) const
{
    std::vector<std::string> candidates;

    if (!m_androidApkAssetRoot || virtualPath.empty())
    {
        return candidates;
    }

    if (virtualPath == "." || virtualPath == "/")
    {
        candidates.emplace_back("assets/worlds/" + m_activeWorldId);
        candidates.emplace_back("assets/engine");
        candidates.emplace_back("assets");
        return candidates;
    }

    const auto appendCandidate = [&candidates](const std::string &candidate)
    {
        if (std::find(candidates.begin(), candidates.end(), candidate) == candidates.end())
        {
            candidates.push_back(candidate);
        }
    };

    appendCandidate("assets/worlds/" + m_activeWorldId + "/" + virtualPath);
    appendCandidate("assets/engine/" + virtualPath);

    for (const char *pWorldId : KnownWorldPackageIds)
    {
        if (m_activeWorldId != pWorldId)
        {
            appendCandidate(std::string("assets/worlds/") + pWorldId + "/" + virtualPath);
        }
    }

    if (virtualPath.starts_with("assets/"))
    {
        appendCandidate(virtualPath);
    }
    else
    {
        appendCandidate("assets/" + virtualPath);
    }

    return candidates;
}

std::string AssetFileSystem::normalizeVirtualPath(const std::string &virtualPath)
{
    std::string normalizedPath = virtualPath;
    std::replace(normalizedPath.begin(), normalizedPath.end(), '\\', '/');

    while (!normalizedPath.empty() && normalizedPath.front() == '/')
    {
        normalizedPath.erase(normalizedPath.begin());
    }

    return normalizedPath;
}

std::string AssetFileSystem::normalizePackageId(
    const std::string &packageId,
    const std::string &defaultPackageId)
{
    std::string normalizedPackageId = packageId;

    normalizedPackageId.erase(
        normalizedPackageId.begin(),
        std::find_if(
            normalizedPackageId.begin(),
            normalizedPackageId.end(),
            [](char character)
            {
                return !std::isspace(static_cast<unsigned char>(character));
            }));
    normalizedPackageId.erase(
        std::find_if(
            normalizedPackageId.rbegin(),
            normalizedPackageId.rend(),
            [](char character)
            {
                return !std::isspace(static_cast<unsigned char>(character));
            }).base(),
        normalizedPackageId.end());

    for (char &character : normalizedPackageId)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));

        if (character == '\\' || character == '/')
        {
            character = '_';
        }
    }

    return normalizedPackageId.empty() ? defaultPackageId : normalizedPackageId;
}

std::vector<std::string> AssetFileSystem::expandPackageAliasCandidates(const std::string &virtualPath)
{
    std::vector<std::string> candidates;

    const auto addAliases = [&virtualPath, &candidates](const auto &aliases)
    {
        for (const VirtualPathAlias &alias : aliases)
        {
            const std::string legacyPrefix = alias.pLegacyPrefix;

            if (virtualPath == legacyPrefix)
            {
                candidates.emplace_back(alias.pPackagePrefix);
                continue;
            }

            const std::string legacyDirectoryPrefix = legacyPrefix + "/";

            if (virtualPath.starts_with(legacyDirectoryPrefix))
            {
                candidates.emplace_back(
                    std::string(alias.pPackagePrefix) + virtualPath.substr(legacyPrefix.size()));
            }
        }
    };

    addAliases(PackagePathAliases);
    addAliases(RootPathAliases);
    return candidates;
}

AssetScaleCategory AssetFileSystem::assetScaleCategoryForVirtualPath(const std::string &virtualPath)
{
    if (virtualPath == TerrainTextureFallbackDirectoryName
        || virtualPath.starts_with(std::string(TerrainTextureFallbackDirectoryName) + "/"))
    {
        return AssetScaleCategory::Terrain;
    }

    if (virtualPath == SkyTextureDirectoryName
        || virtualPath.starts_with(std::string(SkyTextureDirectoryName) + "/"))
    {
        return AssetScaleCategory::Sky;
    }

    for (const TieredAssetDirectory &tieredDirectory : TieredAssetDirectories)
    {
        const std::string canonicalDirectory = tieredDirectory.pCanonicalDirectory;

        if (virtualPath == canonicalDirectory)
        {
            return tieredDirectory.category;
        }

        const std::string directoryPrefix = canonicalDirectory + "/";

        if (virtualPath.starts_with(directoryPrefix))
        {
            return tieredDirectory.category;
        }
    }

    return AssetScaleCategory::Textures;
}

std::string AssetFileSystem::baseTieredVirtualPath(const std::string &virtualPath)
{
    if (virtualPath == TerrainTextureFallbackDirectoryName
        || virtualPath.starts_with(std::string(TerrainTextureFallbackDirectoryName) + "/"))
    {
        if (virtualPath == TerrainTextureFallbackDirectoryName)
        {
            return TexturesDirectoryName;
        }

        return std::string(TexturesDirectoryName)
            + virtualPath.substr(std::string(TerrainTextureFallbackDirectoryName).size());
    }

    if (virtualPath == SkyTextureDirectoryName
        || virtualPath.starts_with(std::string(SkyTextureDirectoryName) + "/"))
    {
        if (virtualPath == SkyTextureDirectoryName)
        {
            return TexturesDirectoryName;
        }

        return std::string(TexturesDirectoryName) + virtualPath.substr(std::string(SkyTextureDirectoryName).size());
    }

    return virtualPath;
}

std::string AssetFileSystem::remapTieredVirtualPath(
    const std::string &virtualPath,
    const AssetScaleProfile &assetScaleProfile)
{
    if (virtualPath == TerrainTextureFallbackDirectoryName
        || virtualPath.starts_with(std::string(TerrainTextureFallbackDirectoryName) + "/"))
    {
        if (virtualPath == TerrainTextureFallbackDirectoryName)
        {
            return TexturesDirectoryName;
        }

        return std::string(TexturesDirectoryName)
            + virtualPath.substr(std::string(TerrainTextureFallbackDirectoryName).size());
    }

    if (virtualPath == SkyTextureDirectoryName
        || virtualPath.starts_with(std::string(SkyTextureDirectoryName) + "/"))
    {
        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(assetScaleProfile, AssetScaleCategory::Sky);
        const std::string remappedDirectory =
            std::string(TexturesDirectoryName) + assetScaleTierDirectorySuffix(assetScaleTier);

        if (virtualPath == SkyTextureDirectoryName)
        {
            return remappedDirectory;
        }

        return remappedDirectory + virtualPath.substr(std::string(SkyTextureDirectoryName).size());
    }

    for (const TieredAssetDirectory &tieredDirectory : TieredAssetDirectories)
    {
        const std::string canonicalDirectory = tieredDirectory.pCanonicalDirectory;

        if (virtualPath != canonicalDirectory && !virtualPath.starts_with(canonicalDirectory + "/"))
        {
            continue;
        }

        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(assetScaleProfile, tieredDirectory.category);

        if (assetScaleTier == AssetScaleTier::X1)
        {
            return virtualPath;
        }

        const std::string directorySuffix = assetScaleTierDirectorySuffix(assetScaleTier);

        if (virtualPath == canonicalDirectory)
        {
            return canonicalDirectory + directorySuffix;
        }

        return canonicalDirectory + directorySuffix + virtualPath.substr(canonicalDirectory.size());
    }

    return virtualPath;
}
}
