#pragma once

#include <optional>
#include <string>

namespace OpenYAMM::Engine
{
enum class AssetScaleTier
{
    X1 = 1,
    X2 = 2,
    X4 = 4
};

const char *assetScaleTierToString(AssetScaleTier assetScaleTier);
std::optional<AssetScaleTier> parseAssetScaleTier(const std::string &value);
int assetScaleTierFactor(AssetScaleTier assetScaleTier);
std::string assetScaleTierDirectorySuffix(AssetScaleTier assetScaleTier);
int scalePhysicalPixelsToLogical(int physicalPixels, AssetScaleTier assetScaleTier);
}
