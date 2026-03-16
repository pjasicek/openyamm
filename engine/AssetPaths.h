#pragma once

#include <filesystem>
#include <string>

namespace OpenYAMM::Engine
{
class AssetPaths
{
public:
    static std::string getDevelopmentAssetRoot();
    static std::filesystem::path getDataDirectory();
    static std::filesystem::path getAnimsDirectory();
    static std::filesystem::path getMusicDirectory();
};
}
