#include "engine/AssetFileSystem.h"

#include <physfs.h>

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

constexpr std::array<const char *, 7> TieredAssetDirectories = {
    "Data/bitmaps",
    "Data/sprites",
    "Data/icons",
    "bitmaps",
    "sprites",
    "icons",
    "textures"
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

constexpr std::array<VirtualPathAlias, 19> PackagePathAliases = {
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
}

AssetFileSystem::AssetFileSystem()
    : m_isInitialized(false)
    , m_activeWorldId(DefaultActiveWorldId)
    , m_assetScaleTier(AssetScaleTier::X1)
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
    shutdown();

    if (!PHYSFS_init(basePath.string().c_str()))
    {
        std::cerr << "PHYSFS_init failed: " << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    m_isInitialized = true;
    m_basePath = basePath;
    m_assetScaleTier = assetScaleTier;
    m_activeWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);

    if (!validateTierDirectories(assetRoot))
    {
        shutdown();
        return false;
    }

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

    m_developmentRoot = assetRoot;
    m_editorDevelopmentRoot = deriveEditorDevelopmentRoot(assetRoot);

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

    if (editorDevelopmentRoot != assetRoot && !mountSearchRoot(editorDevelopmentRoot, false))
    {
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

    if (editorDevelopmentRoot != assetRoot && !mountDevelopmentPackageRoots(editorDevelopmentRoot, m_activeWorldId))
    {
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

    return initialize(basePath, assetRoot, assetScaleTier, activeWorldId);
}

bool AssetFileSystem::mountDevelopmentRoot(const std::filesystem::path &assetRoot)
{
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

    return true;
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

bool AssetFileSystem::mountMergedWorldPackageRoots(
    const std::filesystem::path &assetRoot,
    const std::string &activeWorldId,
    const char *pPackageDirectoryName)
{
    const std::string normalizedWorldId = normalizePackageId(activeWorldId, DefaultActiveWorldId);
    const std::vector<std::filesystem::path> worldPackageRoots =
        collectExistingWorldPackageRoots(assetRoot, pPackageDirectoryName);

    for (const std::filesystem::path &packageRoot : worldPackageRoots)
    {
        const std::string worldId = toLowerAscii(packageRoot.parent_path().filename().string());

        if (worldId == normalizedWorldId)
        {
            continue;
        }

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
    m_searchMounts.clear();
}

bool AssetFileSystem::isInitialized() const
{
    return m_isInitialized;
}

bool AssetFileSystem::validateTierDirectories(const std::filesystem::path &assetRoot) const
{
    if (m_assetScaleTier == AssetScaleTier::X1)
    {
        return true;
    }

    const std::string directorySuffix = assetScaleTierDirectorySuffix(m_assetScaleTier);

    for (const char *pCanonicalDirectory : TieredAssetDirectories)
    {
        const std::filesystem::path tieredDirectory =
            assetRoot / std::filesystem::path(std::string(pCanonicalDirectory) + directorySuffix);

        if (!std::filesystem::exists(tieredDirectory))
        {
            std::cerr << "Selected asset tier " << assetScaleTierToString(m_assetScaleTier)
                      << " is missing required directory: " << tieredDirectory << '\n';
            return false;
        }

        if (!std::filesystem::is_directory(tieredDirectory))
        {
            std::cerr << "Selected asset tier path is not a directory: " << tieredDirectory << '\n';
            return false;
        }
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

    for (const std::string &candidate : aliasCandidates)
    {
        const std::string remappedCandidate = remapTieredVirtualPath(candidate, m_assetScaleTier);

        if (knownPaths.insert(remappedCandidate).second)
        {
            resolvedPaths.push_back(remappedCandidate);
        }
    }

    const std::string remappedLegacyPath = remapTieredVirtualPath(normalizedPath, m_assetScaleTier);

    if (knownPaths.insert(remappedLegacyPath).second)
    {
        resolvedPaths.push_back(remappedLegacyPath);
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

std::string AssetFileSystem::remapTieredVirtualPath(const std::string &virtualPath, AssetScaleTier assetScaleTier)
{
    if (assetScaleTier == AssetScaleTier::X1)
    {
        return virtualPath;
    }

    const std::string directorySuffix = assetScaleTierDirectorySuffix(assetScaleTier);

    for (const char *pCanonicalDirectory : TieredAssetDirectories)
    {
        const std::string canonicalDirectory = pCanonicalDirectory;

        if (virtualPath == canonicalDirectory)
        {
            return canonicalDirectory + directorySuffix;
        }

        const std::string directoryPrefix = canonicalDirectory + "/";

        if (virtualPath.starts_with(directoryPrefix))
        {
            return canonicalDirectory + directorySuffix + virtualPath.substr(canonicalDirectory.size());
        }
    }

    return virtualPath;
}
}
