#include "engine/AssetPaths.h"

namespace OpenYAMM::Engine
{
namespace
{
std::filesystem::path getDevelopmentRootPath()
{
    return std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR);
}
}

std::string AssetPaths::getDevelopmentAssetRoot()
{
    return getDevelopmentRootPath().string();
}

std::filesystem::path AssetPaths::getDataDirectory()
{
    return getDevelopmentRootPath() / "Data";
}

std::filesystem::path AssetPaths::getAnimsDirectory()
{
    return getDevelopmentRootPath() / "Anims";
}

std::filesystem::path AssetPaths::getMusicDirectory()
{
    return getDevelopmentRootPath() / "Music";
}
}
