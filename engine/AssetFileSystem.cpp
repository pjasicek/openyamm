#include "engine/AssetFileSystem.h"

#include <physfs.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::array<const char *, 3> TieredAssetDirectories = {
    "Data/bitmaps",
    "Data/sprites",
    "Data/icons"
};

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
}

AssetFileSystem::AssetFileSystem()
    : m_isInitialized(false)
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
    shutdown();

    if (!PHYSFS_init(basePath.string().c_str()))
    {
        std::cerr << "PHYSFS_init failed: " << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    m_isInitialized = true;
    m_assetScaleTier = assetScaleTier;

    if (!validateTierDirectories(assetRoot))
    {
        shutdown();
        return false;
    }

    if (!mountDevelopmentRoot(assetRoot))
    {
        shutdown();
        return false;
    }

    return true;
}

bool AssetFileSystem::mountDevelopmentRoot(const std::filesystem::path &assetRoot)
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

    if (!PHYSFS_mount(assetRoot.string().c_str(), "/", 1))
    {
        std::cerr << "PHYSFS_mount failed for " << assetRoot << ": "
                  << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    m_developmentRoot = assetRoot;
    return true;
}

bool AssetFileSystem::exists(const std::string &virtualPath) const
{
    if (!isInitialized())
    {
        return false;
    }

    const std::string resolvedPath = resolveVirtualPath(virtualPath);
    return PHYSFS_exists(resolvedPath.c_str()) != 0;
}

std::vector<std::string> AssetFileSystem::enumerate(const std::string &virtualPath) const
{
    std::vector<std::string> entries;

    if (!isInitialized())
    {
        return entries;
    }

    const std::string resolvedPath = resolveVirtualPath(virtualPath);
    char **pEnumeratedEntries = PHYSFS_enumerateFiles(resolvedPath.c_str());
    std::unique_ptr<char *, PhysicsFsListDeleter> pEntryList(pEnumeratedEntries);

    if (pEnumeratedEntries == nullptr)
    {
        return entries;
    }

    for (char **pEntry = pEnumeratedEntries; *pEntry != nullptr; ++pEntry)
    {
        entries.emplace_back(*pEntry);
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

    const std::string resolvedPath = resolveVirtualPath(virtualPath);
    PHYSFS_File *pFile = PHYSFS_openRead(resolvedPath.c_str());

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

const std::filesystem::path &AssetFileSystem::getDevelopmentRoot() const
{
    return m_developmentRoot;
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
    m_developmentRoot.clear();
    m_assetScaleTier = AssetScaleTier::X1;
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
    const std::string normalizedPath = normalizeVirtualPath(virtualPath);
    return remapTieredVirtualPath(normalizedPath, m_assetScaleTier);
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
