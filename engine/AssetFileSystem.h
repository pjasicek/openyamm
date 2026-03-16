#pragma once

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

    bool initialize(const std::filesystem::path &basePath, const std::filesystem::path &assetRoot);
    bool mountDevelopmentRoot(const std::filesystem::path &assetRoot);
    bool exists(const std::string &virtualPath) const;
    std::vector<std::string> enumerate(const std::string &virtualPath) const;
    std::optional<std::vector<uint8_t>> readBinaryFile(const std::string &virtualPath) const;
    std::optional<std::string> readTextFile(const std::string &virtualPath) const;
    std::vector<std::string> getSearchPaths() const;
    const std::filesystem::path &getDevelopmentRoot() const;
    void shutdown();

private:
    bool isInitialized() const;
    static std::string normalizeVirtualPath(const std::string &virtualPath);

    bool m_isInitialized;
    std::filesystem::path m_developmentRoot;
};
}
