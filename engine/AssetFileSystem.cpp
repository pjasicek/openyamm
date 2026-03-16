#include "engine/AssetFileSystem.h"

#include <physfs.h>

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <memory>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
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
{
}

AssetFileSystem::~AssetFileSystem()
{
    shutdown();
}

bool AssetFileSystem::initialize(const std::filesystem::path &basePath, const std::filesystem::path &assetRoot)
{
    shutdown();

    if (!PHYSFS_init(basePath.string().c_str()))
    {
        std::cerr << "PHYSFS_init failed: " << PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()) << '\n';
        return false;
    }

    m_isInitialized = true;

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

    const std::string normalizedPath = normalizeVirtualPath(virtualPath);
    return PHYSFS_exists(normalizedPath.c_str()) != 0;
}

std::vector<std::string> AssetFileSystem::enumerate(const std::string &virtualPath) const
{
    std::vector<std::string> entries;

    if (!isInitialized())
    {
        return entries;
    }

    const std::string normalizedPath = normalizeVirtualPath(virtualPath);
    char **pEnumeratedEntries = PHYSFS_enumerateFiles(normalizedPath.c_str());
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

    const std::string normalizedPath = normalizeVirtualPath(virtualPath);
    PHYSFS_File *pFile = PHYSFS_openRead(normalizedPath.c_str());

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

void AssetFileSystem::shutdown()
{
    if (!isInitialized())
    {
        return;
    }

    PHYSFS_deinit();
    m_isInitialized = false;
    m_developmentRoot.clear();
}

bool AssetFileSystem::isInitialized() const
{
    return m_isInitialized;
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
}
