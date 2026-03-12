#pragma once

#include <filesystem>
#include <string>

namespace OpenYAMM::Engine
{
class AssetPaths
{
public:
    [[nodiscard]] static std::string getDevelopmentAssetRoot();
    [[nodiscard]] static std::filesystem::path getDataDirectory();
    [[nodiscard]] static std::filesystem::path getAnimsDirectory();
    [[nodiscard]] static std::filesystem::path getMusicDirectory();
};
}
