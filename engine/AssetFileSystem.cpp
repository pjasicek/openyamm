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
#include <mutex>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Engine
{
struct AssetReadStream::Impl
{
    ~Impl()
    {
        // PHYSFS_deinit closes every open file itself: a stream outliving it (a house video when an exception unwinds
        // the game) must not close its handle again.
        if (pFile != nullptr && PHYSFS_isInit() != 0)
        {
            PHYSFS_close(pFile);
        }
    }

    PHYSFS_File *pFile = nullptr;
    std::string virtualPath;
};

AssetReadStream::AssetReadStream(std::unique_ptr<Impl> pImpl)
    : m_pImpl(std::move(pImpl))
{
}

AssetReadStream::~AssetReadStream() = default;
AssetReadStream::AssetReadStream(AssetReadStream &&) noexcept = default;
AssetReadStream &AssetReadStream::operator=(AssetReadStream &&) noexcept = default;

bool AssetReadStream::isOpen() const
{
    return m_pImpl != nullptr && m_pImpl->pFile != nullptr;
}

int64_t AssetReadStream::read(void *pBuffer, size_t byteCount)
{
    if (!isOpen() || (pBuffer == nullptr && byteCount > 0))
    {
        return -1;
    }

    if (byteCount == 0)
    {
        return 0;
    }

    return PHYSFS_readBytes(m_pImpl->pFile, pBuffer, byteCount);
}

bool AssetReadStream::seek(uint64_t absoluteOffset)
{
    return isOpen() && PHYSFS_seek(m_pImpl->pFile, absoluteOffset) != 0;
}

int64_t AssetReadStream::tell() const
{
    return isOpen() ? PHYSFS_tell(m_pImpl->pFile) : -1;
}

int64_t AssetReadStream::length() const
{
    return isOpen() ? PHYSFS_fileLength(m_pImpl->pFile) : -1;
}

const std::string &AssetReadStream::virtualPath() const
{
    static const std::string EmptyPath;
    return m_pImpl != nullptr ? m_pImpl->virtualPath : EmptyPath;
}

namespace
{
// Where a package's files live in the virtual tree: the engine at the root, a world under worlds/.
std::string packageMountFolder(const std::string &package)
{
    return package == "engine" ? package : "worlds/" + package;
}

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
constexpr const char *SpritesDirectoryName = "sprites";

// PhysFS paths and the log are UTF-8, with forward slashes.
std::string utf8String(const std::filesystem::path &path)
{
    const std::u8string text = path.generic_u8string();
    return std::string(text.begin(), text.end());
}
constexpr const char *SkyTextureDirectoryName = "sky_textures";
constexpr const char *LegacyDirectoryName = "_legacy";
constexpr const char *SingleAssetPackageName = "assets.zip";
constexpr std::array<const char *, 3> KnownWorldPackageIds = {"mm6", "mm7", "mm8"};

struct TieredAssetDirectory
{
    const char *pCanonicalDirectory;
    AssetScaleCategory category;
};

constexpr std::array<TieredAssetDirectory, 5> TieredAssetDirectories = {
    TieredAssetDirectory{"Data/bitmaps", AssetScaleCategory::Textures},
    TieredAssetDirectory{"Data/icons", AssetScaleCategory::Icons},
    TieredAssetDirectory{"bitmaps", AssetScaleCategory::Textures},
    TieredAssetDirectory{"textures", AssetScaleCategory::Textures},
    TieredAssetDirectory{"icons", AssetScaleCategory::Icons}
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

constexpr std::array<VirtualPathAlias, 31> PackagePathAliases = {
    VirtualPathAlias{"engine/audio", "audio"},
    VirtualPathAlias{"engine/data_tables/english", "data_tables/english"},
    VirtualPathAlias{"engine/data_tables", "data_tables"},
    VirtualPathAlias{"engine/events", "events"},
    VirtualPathAlias{"engine/fonts/english_text", "fonts/english_text"},
    VirtualPathAlias{"engine/fonts", "fonts"},
    VirtualPathAlias{"engine/icons", "icons"},
    VirtualPathAlias{"engine/music", "music"},
    VirtualPathAlias{"engine/models", "models"},
    VirtualPathAlias{"engine/rendering", "rendering"},
    VirtualPathAlias{"engine/scripts", "scripts"},
    VirtualPathAlias{"engine/sprites", "sprites"},
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
    VirtualPathAlias{"Data/bitmaps", "textures"},
    VirtualPathAlias{"Data/bitmaps", "effects"},
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

struct AssetFileSystem::LookupCache
{
    struct Name
    {
        std::string spelling;
        bool ambiguous = false;
    };
    std::mutex mutex;
    std::unordered_map<std::string, std::unordered_map<std::string, Name>> directories;
    std::unordered_map<std::string, std::optional<std::string>> files;
    // enumerate() results by virtual directory: a mounted directory lists through every mount and alias, which
    // costs milliseconds for the large merged ones (icons, bitmaps, sprites).
    std::unordered_map<std::string, std::vector<std::string>> listings;
};

std::optional<std::string> AssetFileSystem::findCaseInsensitiveVirtualPath(const std::string &virtualPath) const
{
    const std::filesystem::path path(virtualPath);
    const std::string parent = path.parent_path().generic_string();
    const std::string name = toLowerAscii(path.filename().string());
    if (name.empty())
    {
        return std::nullopt;
    }
    const std::string directory = parent.empty() ? "." : parent;
    std::lock_guard lock(m_pLookupCache->mutex);
    auto [entry, inserted] = m_pLookupCache->directories.try_emplace(directory);
    if (inserted)
    {
        char **pEntries = PHYSFS_enumerateFiles(directory.c_str());
        std::unique_ptr<char *, PhysicsFsListDeleter> pList(pEntries);
        if (pEntries != nullptr)
        {
            for (char **pEntry = pEntries; *pEntry != nullptr; ++pEntry)
            {
                auto [file, unique] = entry->second.try_emplace(toLowerAscii(*pEntry), LookupCache::Name{*pEntry});
                if (!unique && file->second.spelling != *pEntry)
                {
                    const auto origin = [&parent](const std::string &spelling)
                    {
                        const std::string path = parent.empty() ? spelling : parent + "/" + spelling;
                        const char *pRoot = PHYSFS_getRealDir(path.c_str());
                        return pRoot != nullptr ? std::string(pRoot) : std::string();
                    };
                    const std::string selectedRoot = origin(file->second.spelling);
                    const std::string candidateRoot = origin(*pEntry);
                    if (selectedRoot == candidateRoot)
                    {
                        std::cerr << "Ambiguous asset filename in " << selectedRoot << "/" << directory
                                  << ": " << *pEntry << '\n';
                        file->second.ambiguous = true;
                    }
                    else
                    {
                        const auto priority = [this](const std::string &root)
                        {
                            return std::find_if(m_searchMounts.begin(), m_searchMounts.end(),
                                [&root](const SearchMount &mount) { return mount.root.string() == root; });
                        };
                        if (priority(candidateRoot) < priority(selectedRoot))
                        {
                            file->second = {*pEntry, false};
                        }
                    }
                }
            }
        }
    }
    const auto file = entry->second.find(name);
    if (file == entry->second.end() || file->second.ambiguous)
    {
        return std::nullopt;
    }
    return parent.empty() ? file->second.spelling : parent + "/" + file->second.spelling;
}

void AssetFileSystem::refreshLookupCache() const
{
    std::lock_guard lock(m_pLookupCache->mutex);
    m_pLookupCache->directories.clear();
    m_pLookupCache->files.clear();
    m_pLookupCache->listings.clear();
    ++m_contentGeneration;
}

uint64_t AssetFileSystem::contentGeneration() const
{
    return m_contentGeneration;
}

AssetFileSystem::AssetFileSystem()
    : m_isInitialized(false)
    , m_activeWorldId(DefaultActiveWorldId)
    , m_assetScaleTier(AssetScaleTier::X1)
    , m_assetScaleProfile(createUniformAssetScaleProfile(AssetScaleTier::X1))
    , m_androidApkAssetRoot(false)
    , m_pLookupCache(std::make_unique<LookupCache>())
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
    return initialize(basePath, assetRoot, assetScaleTier, assetScaleProfile, activeWorldId, {});
}

bool AssetFileSystem::initialize(
    const std::filesystem::path &basePath,
    const std::filesystem::path &assetRoot,
    AssetScaleTier assetScaleTier,
    const AssetScaleProfile &assetScaleProfile,
    const std::string &activeWorldId,
    const InstalledContentOptions &installedContentOptions)
{
    shutdown();

    if (!initializePhysicsFs(basePath))
    {
        std::cerr << "PHYSFS_init failed: " << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    // Asset trees contain no symbolic links. With links disallowed PhysFS would lstat every entry of a directory it
    // lists, only to filter them out: about 7 microseconds an entry, 0.25 s for the large merged directories.
    PHYSFS_permitSymbolicLinks(1);

    m_isInitialized = true;
    m_basePath = basePath;
    m_assetScaleTier = assetScaleTier;
    m_assetScaleProfile = assetScaleProfile;
    m_installedContentOptions = installedContentOptions;
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

        if (!mountLanguagePack(true) || !mountMods(m_installedContentOptions.modsRoot))
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

        if (!mountExtraDevelopmentRoot(m_installedContentOptions.extraMountRoot))
        {
            shutdown();
            return false;
        }
    }

    // Mods mount after the pack in a release (a player's mod still wins); Android and development roots have no mods.
    if (!packagedAssetRoot || androidApkAssetRoot)
    {
        if (!mountLanguagePack(packagedAssetRoot))
        {
            shutdown();
            return false;
        }
    }

    if (!loadIconPackagePolicy())
    {
        shutdown();
        return false;
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
    const InstalledContentOptions installedContentOptions = m_installedContentOptions;

    return initialize(basePath, assetRoot, assetScaleTier, assetScaleProfile, activeWorldId, installedContentOptions);
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

bool AssetFileSystem::mountExtraDevelopmentRoot(const std::filesystem::path &extraRoot)
{
    if (extraRoot.empty())
    {
        return true;
    }

    std::error_code error;

    if (!std::filesystem::is_directory(extraRoot, error))
    {
        std::cerr << "Extra mount is not a directory: " << extraRoot << '\n';
        return false;
    }

    // The same places a development root's files are read from, each in front of the root's own: the folder itself,
    // its engine and active world packages, and the map folders of every world merged by name. The active world's
    // are mounted last, so they are found first.
    if (!mountSearchRoot(extraRoot, false))
    {
        return false;
    }

    const std::filesystem::path engineRoot = extraRoot / EngineDevelopmentRootName;
    const std::filesystem::path worldsRoot = extraRoot / WorldsDevelopmentRootName;
    const std::filesystem::path activeWorldRoot = worldsRoot / m_activeWorldId;
    std::vector<std::filesystem::path> worldRoots;

    for (std::filesystem::directory_iterator entry(worldsRoot, error), end; !error && entry != end;
         entry.increment(error))
    {
        std::error_code typeError;

        if (entry->is_directory(typeError) && entry->path() != activeWorldRoot)
        {
            worldRoots.push_back(entry->path());
        }
    }

    std::sort(worldRoots.begin(), worldRoots.end());

    if (std::filesystem::is_directory(engineRoot, error) && !mountSearchRoot(engineRoot, false))
    {
        return false;
    }

    if (std::filesystem::is_directory(activeWorldRoot, error))
    {
        if (!mountSearchRoot(activeWorldRoot, false))
        {
            return false;
        }

        worldRoots.push_back(activeWorldRoot);
    }

    const AssetScaleTier textureTier = assetScaleTierForCategory(m_assetScaleProfile, AssetScaleCategory::Textures);
    std::vector<std::string> mergedDirectoryNames = {MapsDirectoryName, EventsDirectoryName, TexturesDirectoryName};

    if (textureTier != AssetScaleTier::X1)
    {
        mergedDirectoryNames.push_back(TexturesDirectoryName + assetScaleTierDirectorySuffix(textureTier));
    }

    for (const std::filesystem::path &worldRoot : worldRoots)
    {
        for (const std::string &directoryName : mergedDirectoryNames)
        {
            const std::filesystem::path packageRoot = worldRoot / directoryName;

            if (std::filesystem::is_directory(packageRoot, error)
                && !mountSearchRootAt(packageRoot, "/" + directoryName, false))
            {
                return false;
            }
        }
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
        || std::filesystem::is_regular_file(assetRoot / AssetPackIndexFileName);
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

    // The APK itself stays mounted for its own files (licenses); content comes from the packs stored inside it.
    if (!PHYSFS_mount(pApkPath, "/", 1))
    {
        std::cerr << "PHYSFS_mount failed for Android APK " << pApkPath << ": "
                  << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    refreshLookupCache();
    SearchMount searchMount;
    searchMount.root = pApkPath;
    searchMount.mountPoint = "";
    searchMount.archive = true;
    m_searchMounts.push_back(searchMount);
    m_activeWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);
    m_androidApkAssetRoot = true;

    const std::string apkAssets = "assets/";
    std::string error;
    std::optional<AssetPackIndex> index;

    if (PHYSFS_File *pIndexFile = PHYSFS_openRead((apkAssets + AssetPackIndexFileName).c_str()))
    {
        std::string text(size_t(std::max<PHYSFS_sint64>(PHYSFS_fileLength(pIndexFile), 0)), '\0');
        const bool complete = PHYSFS_readBytes(pIndexFile, text.data(), text.size()) == PHYSFS_sint64(text.size());
        PHYSFS_close(pIndexFile);
        index = complete ? parseAssetPackIndex(text, error) : std::nullopt;
    }

    if (!index)
    {
        std::cerr << "The APK carries no usable content index: " << error << '\n';
        return false;
    }

    const std::string storeRoot = apkAssets + index->store + "/";
    const bool mounted = mountContentPacks(
        *index,
        m_activeWorldId,
        [this, &storeRoot, pApkPath](const AssetPackRecord &pack, bool appendToPath)
        {
            // Packs are stored uncompressed in the APK (noCompress "zip"), so PhysicsFS reads them in place.
            const std::string path = storeRoot + pack.file;

            // The APK ships no language packs: a language's packs are downloaded into app storage.
            if (!pack.language.empty() && !PHYSFS_exists(path.c_str()))
            {
                m_languagePacksMissing = true;
                return true;
            }

            PHYSFS_File *pPackFile = PHYSFS_openRead(path.c_str());

            if (pPackFile == nullptr || PHYSFS_fileLength(pPackFile) != PHYSFS_sint64(pack.size))
            {
                std::cerr << "Missing or damaged content pack in the APK: " << path << '\n';
                PHYSFS_close(pPackFile);
                return false;
            }

            const std::string mountName = std::string(pApkPath) + "/" + path;

            if (!PHYSFS_mountHandle(pPackFile, mountName.c_str(), pack.mount.c_str(), appendToPath ? 1 : 0))
            {
                std::cerr << "PHYSFS_mountHandle failed for " << path << ": "
                          << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
                PHYSFS_close(pPackFile);
                return false;
            }

            SearchMount packMount;
            packMount.root = mountName;
            packMount.mountPoint = normalizeVirtualPath(pack.mount);
            packMount.packageMountPoint = packageMountFolder(pack.package);
            packMount.archive = true;
            packMount.languagePack = !pack.language.empty();
            recordSearchMount(std::move(packMount), appendToPath);
            return true;
        });

    if (!mounted)
    {
        return false;
    }

    std::cout << "Mounted " << index->packs.size() << " content packs from the Android APK: " << pApkPath << '\n';
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
    if (isZipArchivePath(assetRoot))
    {
        return mountSearchRoot(assetRoot, true);
    }

    if (!std::filesystem::is_directory(assetRoot))
    {
        std::cerr << "Packaged asset root does not exist: " << assetRoot << '\n';
        return false;
    }

    if (std::filesystem::exists(assetRoot / SingleAssetPackageName))
    {
        return mountPackageArchiveIfPresent(assetRoot / SingleAssetPackageName, true);
    }

    std::string error;
    const std::optional<AssetPackIndex> index = loadAssetPackIndex(assetRoot / AssetPackIndexFileName, error);
    const std::filesystem::path storeRoot = assetRoot / (index ? index->store : std::string());

    // Kept modified packs have sizes of their own; only a missing one still makes the content unusable.
    if (!index
        || !(m_installedContentOptions.acceptModifiedPacks ? assetPackFilesExist(*index, storeRoot, error)
                                                           : validateAssetPackFiles(*index, storeRoot, error)))
    {
        std::cerr << "Installed content is unusable (" << error << "); reinstall or verify the game files.\n";
        return false;
    }

    m_missingLanguageBytes.clear();

    for (const std::string &language : assetPackLanguages(*index))
    {
        m_missingLanguageBytes.emplace_back(language, Engine::missingLanguagePackBytes(*index, storeRoot, language));
    }

    return mountContentPacks(
        *index,
        activeWorldId,
        [this, &storeRoot](const AssetPackRecord &pack, bool appendToPath)
        {
            const std::string packageMount = "/" + packageMountFolder(pack.package);
            std::error_code fileError;

            // A language's packs are optional: downloaded only once the player chooses it.
            if (!pack.language.empty() && !std::filesystem::is_regular_file(storeRoot / pack.file, fileError))
            {
                std::cout << "Language pack not installed: " << pack.id << '\n';
                m_languagePacksMissing = true;
                return true;
            }

            return mountSearchRootAt(storeRoot / pack.file, pack.mount, appendToPath, packageMount,
                                     !pack.language.empty());
        });
}

bool AssetFileSystem::mountContentPacks(
    const AssetPackIndex &index,
    const std::string &activeWorldId,
    const std::function<bool(const AssetPackRecord &, bool appendToPath)> &mountPack)
{
    const std::string normalizedWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);

    // Packs of one package never overlap, so only the order between packages matters: the active world first (as a
    // single world archive was), then the engine, then the other worlds for unqualified legacy requests.
    for (const AssetPackRecord &pack : index.packs)
    {
        if (pack.language.empty() && pack.package == normalizedWorldId && !mountPack(pack, false))
        {
            return false;
        }
    }

    for (const bool engine : {true, false})
    {
        for (const AssetPackRecord &pack : index.packs)
        {
            if (pack.language.empty() && (pack.package == "engine") == engine && pack.package != normalizedWorldId
                && !mountPack(pack, true))
            {
                return false;
            }
        }
    }

    // The interface language's fonts, sounds and videos in front of the game's (they replace files of the packs
    // above); the other languages' stay unmounted. A language whose packs were never downloaded has none here.
    const std::string &languageId = m_installedContentOptions.languageId;

    for (const AssetPackRecord &pack : index.packs)
    {
        if (!languageId.empty() && pack.language == languageId && !mountPack(pack, false))
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

bool AssetFileSystem::mountMods(const std::filesystem::path &modsRoot)
{
    std::error_code error;

    if (modsRoot.empty() || !std::filesystem::is_directory(modsRoot, error))
    {
        return true;
    }

    // Each folder mirrors a package root as the packs mount it: mods/engine/data_tables/x.txt replaces
    // engine/data_tables/x.txt. Unreadable entries are skipped, never thrown at the start.
    std::vector<std::pair<std::filesystem::path, std::string>> folders;

    for (std::filesystem::directory_iterator entry(modsRoot, error), end; !error && entry != end;
         entry.increment(error))
    {
        const std::string name = utf8String(entry->path().filename());
        std::error_code typeError;

        if (name == EngineDevelopmentRootName && entry->is_directory(typeError))
        {
            folders.emplace_back(entry->path(), EngineDevelopmentRootName);
            continue;
        }

        if (name == WorldsDevelopmentRootName && entry->is_directory(typeError))
        {
            std::error_code worldError;

            for (std::filesystem::directory_iterator world(entry->path(), worldError); !worldError && world != end;
                 world.increment(worldError))
            {
                if (world->is_directory(typeError))
                {
                    folders.emplace_back(world->path(), name + "/" + utf8String(world->path().filename()));
                }
                else
                {
                    std::cout << "Mods: ignoring " << utf8String(world->path())
                              << ": mods/worlds holds one folder per world\n";
                }
            }

            continue;
        }

        std::cout << "Mods: ignoring " << utf8String(entry->path()) << ": mods holds only engine and worlds\n";
    }

    std::sort(folders.begin(), folders.end());
    // Enough to recognise a mod in a log; someone who extracted a whole pack learns the count.
    constexpr size_t LoggedFileCount = 100;
    size_t fileCount = 0;

    for (const auto &[folder, package] : folders)
    {
        std::vector<std::string> files;
        std::error_code fileError;

        for (std::filesystem::recursive_directory_iterator file(folder, fileError), end; !fileError && file != end;
             file.increment(fileError))
        {
            std::error_code typeError;

            if (file->is_regular_file(typeError))
            {
                files.push_back(package + "/" + utf8String(file->path().lexically_relative(folder)));
            }
        }

        if (files.empty())
        {
            continue;
        }

        std::sort(files.begin(), files.end());

        // Before mounting, so the game's own files are what the mod files are compared with.
        for (size_t index = 0; index < files.size() && fileCount + index < LoggedFileCount; ++index)
        {
            const std::string &file = files[index];
            const bool replaces = PHYSFS_exists(file.c_str()) != 0;
            const std::optional<std::string> spelling = replaces ? std::nullopt : findCaseInsensitiveVirtualPath(file);
            std::cout << "Mods: " << file;

            if (replaces)
            {
                std::cout << " replaces the game's file\n";
            }
            else if (spelling)
            {
                std::cout << " may be ignored: name it exactly like the game's file, " << *spelling << '\n';
            }
            else
            {
                std::cout << " is a new file\n";
            }
        }

        fileCount += files.size();

        if (!mountSearchRootAt(folder, "/" + package, false))
        {
            return false;
        }
    }

    if (fileCount > LoggedFileCount)
    {
        std::cout << "Mods: and " << fileCount - LoggedFileCount << " more files\n";
    }

    if (fileCount > 0)
    {
        std::cout << "Mods: " << fileCount << (fileCount == 1 ? " file" : " files") << " from " << utf8String(modsRoot)
                  << '\n';
    }

    return true;
}

bool AssetFileSystem::mountLanguagePack(bool packagedRoot)
{
    std::error_code error;
    const std::filesystem::path &userLanguagesRoot = m_installedContentOptions.userLanguagesRoot;

    if (!userLanguagesRoot.empty() && std::filesystem::is_directory(userLanguagesRoot, error)
        && !mountSearchRootAt(userLanguagesRoot, "/languages", false))
    {
        return false;
    }

    const std::string &languageId = m_installedContentOptions.languageId;

    if (languageId.empty() || languageId == "en" || languageId.find_first_of("/\\.") != std::string::npos)
    {
        return true;
    }

    const std::optional<std::filesystem::path> pack = resolvePhysicalPath("languages/" + languageId);

    if (!pack || !std::filesystem::is_directory(*pack, error))
    {
        return true;
    }

    // The pack mirrors the game's tree like mods/, but only these folders mount: its text goes through its
    // translation files, never through replaced game files. A release reads them at their package path
    // (/engine/fonts, /worlds/mm7/audio); a development root at the merged folder (/fonts, /audio:
    // mountMerged*Roots), where only the active world's mount. PhysFS mounts a folder once, so each takes one place.
    constexpr std::array<const char *, 3> OverlayDirectories = {"fonts", "audio", "videos"};
    const auto mountOverlay = [this, &error, packagedRoot](const std::filesystem::path &folder,
                                                            const std::string &packagePoint, const char *pDirectory)
    {
        if (!std::filesystem::is_directory(folder, error))
        {
            return true;
        }

        const std::string mountPoint = packagedRoot ? packagePoint + "/" + pDirectory : std::string("/") + pDirectory;
        std::cout << "Language: " << utf8String(folder) << " over " << mountPoint << '\n';
        return mountSearchRootAt(folder, mountPoint, false);
    };

    for (const char *pDirectory : OverlayDirectories)
    {
        if (!mountOverlay(*pack / EngineDevelopmentRootName / pDirectory, "/engine", pDirectory))
        {
            return false;
        }
    }

    const std::filesystem::path worldsRoot = *pack / WorldsDevelopmentRootName;

    for (std::filesystem::directory_iterator world(worldsRoot, error), end; packagedRoot && !error && world != end;
         world.increment(error))
    {
        const std::string worldId = utf8String(world->path().filename());

        // The active world's files mount last, in front of the engine's and the other worlds'.
        if (worldId == m_activeWorldId)
        {
            continue;
        }

        for (const char *pDirectory : {"audio", "videos"})
        {
            if (!mountOverlay(world->path() / pDirectory, "/worlds/" + worldId, pDirectory))
            {
                return false;
            }
        }
    }

    error.clear();

    for (const char *pDirectory : {"audio", "videos"})
    {
        if (!mountOverlay(worldsRoot / m_activeWorldId / pDirectory, "/worlds/" + m_activeWorldId, pDirectory))
        {
            return false;
        }
    }

    return true;
}

bool AssetFileSystem::mountSearchRoot(const std::filesystem::path &assetRoot, bool appendToPath)
{
    return mountSearchRootAt(assetRoot, "/", appendToPath);
}

bool AssetFileSystem::mountSearchRootAt(
    const std::filesystem::path &assetRoot,
    const std::string &mountPoint,
    bool appendToPath,
    const std::string &packageMountPoint,
    bool languagePack)
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
    searchMount.packageMountPoint =
        packageMountPoint.empty() ? searchMount.mountPoint : normalizeVirtualPath(packageMountPoint);
    searchMount.archive = isZipArchivePath(assetRoot);
    searchMount.languagePack = languagePack;
    recordSearchMount(std::move(searchMount), appendToPath);
    return true;
}

void AssetFileSystem::recordSearchMount(SearchMount searchMount, bool appendToPath)
{
    if (appendToPath)
    {
        m_searchMounts.push_back(std::move(searchMount));
    }
    else
    {
        m_searchMounts.insert(m_searchMounts.begin(), std::move(searchMount));
    }

    refreshLookupCache();
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
        && mountMergedWorldScaledPackageRoots(
            assetRoot,
            activeWorldId,
            TexturesDirectoryName,
            assetScaleTierForCategory(m_assetScaleProfile, AssetScaleCategory::Textures))
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

std::optional<std::string> AssetFileSystem::resolveExistingFilePath(const std::string &virtualPath) const
{
    if (!isInitialized())
    {
        return std::nullopt;
    }
    {
        std::lock_guard lock(m_pLookupCache->mutex);
        const auto file = m_pLookupCache->files.find(virtualPath);
        if (file != m_pLookupCache->files.end())
        {
            return file->second;
        }
    }
    std::optional<std::string> result;
    for (const std::string &candidate : resolveVirtualPathCandidates(virtualPath))
    {
        PHYSFS_Stat stat = {};
        if (PHYSFS_stat(candidate.c_str(), &stat) && stat.filetype == PHYSFS_FILETYPE_REGULAR)
        {
            result = candidate;
            break;
        }
        const std::optional<std::string> actualPath = findCaseInsensitiveVirtualPath(candidate);
        if (actualPath && PHYSFS_stat(actualPath->c_str(), &stat) && stat.filetype == PHYSFS_FILETYPE_REGULAR)
        {
            result = actualPath;
            break;
        }
    }
    std::lock_guard lock(m_pLookupCache->mutex);
    m_pLookupCache->files.emplace(virtualPath, result);
    return result;
}

std::optional<AssetFileInfo> AssetFileSystem::fileInfo(const std::string &virtualPath) const
{
    const std::optional<std::string> path = resolveExistingFilePath(virtualPath);
    PHYSFS_Stat stat = {};
    if (!path || !PHYSFS_stat(path->c_str(), &stat) || stat.filesize < 0)
    {
        return std::nullopt;
    }
    const char *pRoot = PHYSFS_getRealDir(path->c_str());
    const auto mount = std::find_if(m_searchMounts.begin(), m_searchMounts.end(),
        [pRoot](const SearchMount &entry) { return pRoot != nullptr && entry.root.string() == pRoot; });
    return AssetFileInfo{uint64_t(stat.filesize), stat.modtime, mount != m_searchMounts.end() && mount->archive};
}

std::vector<std::string> AssetFileSystem::enumerate(const std::string &virtualPath) const
{
    std::vector<std::string> entries;
    std::unordered_set<std::string> knownEntries;

    if (!isInitialized())
    {
        return entries;
    }

    {
        std::lock_guard lock(m_pLookupCache->mutex);
        const auto listing = m_pLookupCache->listings.find(virtualPath);
        if (listing != m_pLookupCache->listings.end())
        {
            return listing->second;
        }
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
    std::lock_guard lock(m_pLookupCache->mutex);
    m_pLookupCache->listings.try_emplace(virtualPath, entries);
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

std::unique_ptr<AssetReadStream> AssetFileSystem::openReadStream(const std::string &virtualPath) const
{
    const std::optional<std::string> resolved = resolveExistingFilePath(virtualPath);
    if (!resolved)
    {
        return nullptr;
    }
    PHYSFS_File *pFile = PHYSFS_openRead(resolved->c_str());
    if (pFile == nullptr)
    {
        return nullptr;
    }
    std::unique_ptr<AssetReadStream::Impl> pImpl = std::make_unique<AssetReadStream::Impl>();
    pImpl->pFile = pFile;
    pImpl->virtualPath = *resolved;
    return std::unique_ptr<AssetReadStream>(new AssetReadStream(std::move(pImpl)));
}

std::optional<std::vector<uint8_t>> AssetFileSystem::readBinaryFile(const std::string &virtualPath) const
{
    std::unique_ptr<AssetReadStream> pStream = openReadStream(virtualPath);

    if (pStream == nullptr)
    {
        return std::nullopt;
    }

    const int64_t fileLength = pStream->length();

    if (fileLength < 0)
    {
        return std::nullopt;
    }

    std::vector<uint8_t> contents(static_cast<size_t>(fileLength));
    const int64_t bytesRead = pStream->read(contents.data(), contents.size());

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
    const std::string normalized = normalizeVirtualPath(virtualPath);
    const AssetScaleCategory category = assetScaleCategoryForVirtualPath(normalized);
    if (category == AssetScaleCategory::Icons && !m_iconPackages.empty())
    {
        std::string package = "engine";
        if (normalized.starts_with("worlds/"))
        {
            package = normalized.substr(0, normalized.find('/', 7));
        }
        for (const auto &[root, tier] : m_iconPackages)
        {
            if (root == package)
            {
                return tier;
            }
        }
    }
    return getAssetScaleTier(category);
}

bool AssetFileSystem::languagePacksMissing() const
{
    return m_languagePacksMissing;
}

uint64_t AssetFileSystem::missingLanguagePackBytes(const std::string &languageId) const
{
    for (const auto &[language, bytes] : m_missingLanguageBytes)
    {
        if (language == languageId)
        {
            return bytes;
        }
    }

    return 0;
}

const AssetScaleProfile &AssetFileSystem::getAssetScaleProfile() const
{
    return m_assetScaleProfile;
}

void AssetFileSystem::shutdown()
{
    refreshLookupCache();
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
    m_installedContentOptions = {};
    m_iconPackages.clear();
    m_searchMounts.clear();
    m_androidApkAssetRoot = false;
    m_languagePacksMissing = false;
    m_missingLanguageBytes.clear();
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

    constexpr std::array<RequiredTieredDirectory, 2> RequiredTieredDirectories = {
        RequiredTieredDirectory{AssetScaleCategory::Textures, "textures", "Data/bitmaps"},
        RequiredTieredDirectory{AssetScaleCategory::Icons, "icons", "Data/icons"}
    };

    for (const RequiredTieredDirectory &requiredDirectory : RequiredTieredDirectories)
    {
        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(m_assetScaleProfile, requiredDirectory.category);

        if (assetScaleTier == AssetScaleTier::X1
            || (requiredDirectory.category == AssetScaleCategory::Icons && m_assetScaleProfile.preferRestoredIcons))
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

    constexpr std::array<RequiredTieredDirectory, 2> RequiredTieredDirectories = {
        RequiredTieredDirectory{AssetScaleCategory::Textures, "textures", "Data/bitmaps"},
        RequiredTieredDirectory{AssetScaleCategory::Icons, "icons", "Data/icons"}
    };

    for (const RequiredTieredDirectory &requiredDirectory : RequiredTieredDirectories)
    {
        const AssetScaleTier assetScaleTier =
            assetScaleTierForCategory(m_assetScaleProfile, requiredDirectory.category);

        if (assetScaleTier == AssetScaleTier::X1
            || (requiredDirectory.category == AssetScaleCategory::Icons && m_assetScaleProfile.preferRestoredIcons))
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

bool AssetFileSystem::loadIconPackagePolicy()
{
    const std::optional<std::string> text = readTextFile("engine/icon_packages.txt");
    if (!text)
    {
        return true;
    }
    std::istringstream stream(*text);
    std::string line;
    std::unordered_set<std::string> packages;
    while (std::getline(stream, line))
    {
        std::istringstream fields(line);
        std::string package;
        std::string tierName;
        std::string extra;
        if (!(fields >> package) || package.starts_with("#"))
        {
            continue;
        }
        fields >> tierName;
        const std::optional<AssetScaleTier> tier = parseAssetScaleTier(tierName);
        const bool validWorld = package.starts_with("worlds/") && package.size() > 7
            && package.find('/', 7) == std::string::npos && package.find("..") == std::string::npos;
        if ((!validWorld && package != "engine") || !tier || (fields >> extra)
            || !packages.insert(package).second)
        {
            std::cerr << "Invalid icon package policy: " << line << '\n';
            return false;
        }
        m_iconPackages.emplace_back(package, *tier);
    }
    if (!packages.contains("engine"))
    {
        std::cerr << "Icon package policy must declare the engine root\n";
        return false;
    }
    // Match ordinary package precedence: active world, base, then the other declared worlds.
    std::stable_sort(m_iconPackages.begin(), m_iconPackages.end(), [this](const auto &left, const auto &right)
    {
        const auto priority = [this](const std::string &package)
        {
            return package == "worlds/" + m_activeWorldId ? 0 : package == "engine" ? 1 : 2;
        };
        return priority(left.first) < priority(right.first);
    });
    refreshLookupCache();
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
    const bool packageQualified = normalizedPath.starts_with("engine/") || normalizedPath.starts_with("worlds/");
    if (!m_iconPackages.empty())
    {
        std::string package;
        std::string relative = normalizedPath;
        if (normalizedPath.starts_with("engine/"))
        {
            package = "engine";
            relative = normalizedPath.substr(7);
        }
        else if (normalizedPath.starts_with("worlds/"))
        {
            const size_t separator = normalizedPath.find('/', 7);
            if (separator != std::string::npos)
            {
                package = normalizedPath.substr(0, separator);
                relative = normalizedPath.substr(separator + 1);
            }
        }
        if (relative.starts_with("Data/"))
        {
            relative = relative.substr(5);
        }
        const size_t separator = relative.find('/');
        const std::string directory = relative.substr(0, separator);
        if (directory == "icons" || directory == "icons_x2" || directory == "icons_x4")
        {
            const std::string suffix = separator == std::string::npos ? "" : relative.substr(separator);
            for (const auto &[root, tier] : m_iconPackages)
            {
                if (!package.empty() && root != package)
                {
                    continue;
                }
                resolvedPaths.push_back(root + "/icons" + assetScaleTierDirectorySuffix(tier) + suffix);
            }
            // No native or other-package fallback for a qualified icon request.
            return resolvedPaths;
        }
    }
    const std::vector<std::string> aliasCandidates = expandPackageAliasCandidates(normalizedPath);

    const auto appendCandidate = [&resolvedPaths, &knownPaths](const std::string &candidate)
    {
        if (knownPaths.insert(candidate).second)
        {
            resolvedPaths.push_back(candidate);
        }
    };

    const auto appendPackageCandidates =
        [this, &appendCandidate, packageQualified](const std::string &candidate)
    {
        if (!packageQualified)
        {
            // Once per package, in mount precedence; a package's content packs share its root. A language's packs,
            // mounted in front of all others, would put their package first (an MM7 game read MM8's world.yml).
            for (const SearchMount &mount : m_searchMounts)
            {
                if (mount.archive && !mount.languagePack)
                {
                    appendCandidate(
                        mount.packageMountPoint.empty() ? candidate : mount.packageMountPoint + "/" + candidate);
                }
            }
        }
        appendCandidate(candidate);
    };

    const auto appendPathWithTierFallbacks =
        [this, &appendPackageCandidates](const std::string &candidate)
    {
        appendPackageCandidates(remapTieredVirtualPath(candidate, m_assetScaleProfile));
        appendPackageCandidates(baseTieredVirtualPath(candidate));
    };

    if (packageQualified)
    {
        appendPathWithTierFallbacks(normalizedPath);
    }

    for (const std::string &candidate : aliasCandidates)
    {
        appendPathWithTierFallbacks(candidate);
    }

    if (!packageQualified)
    {
        appendPathWithTierFallbacks(normalizedPath);
    }

    return resolvedPaths;
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
    if (virtualPath.starts_with("engine/"))
    {
        return assetScaleCategoryForVirtualPath(virtualPath.substr(7));
    }
    if (virtualPath.starts_with("worlds/"))
    {
        const size_t separator = virtualPath.find('/', 7);
        if (separator != std::string::npos)
        {
            return assetScaleCategoryForVirtualPath(virtualPath.substr(separator + 1));
        }
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
    if (virtualPath.starts_with("engine/"))
    {
        return "engine/" + remapTieredVirtualPath(virtualPath.substr(7), assetScaleProfile);
    }
    if (virtualPath.starts_with("worlds/"))
    {
        const size_t separator = virtualPath.find('/', 7);
        if (separator != std::string::npos)
        {
            return virtualPath.substr(0, separator + 1)
                + remapTieredVirtualPath(virtualPath.substr(separator + 1), assetScaleProfile);
        }
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
