#pragma once

#include "game/render/AnimatedModelAsset.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9AnimatedModelMaterialRef
{
    size_t index = 0;
    std::string texture;
    std::string runtimeTexture;
    std::string previewTexture;
    bool alphaMask = false;
    float alphaCutoff = 0.5f;
    bool doubleSided = false;
};

struct Mm9AnimatedModelAnimationEvent
{
    uint32_t timeMs = 0;
    std::string event;
};

struct Mm9AnimatedModelAnimationInfo
{
    std::string name;
    uint32_t durationMs = 0;
    uint32_t keyframes = 0;
    uint32_t interpolationTimeMs = 0;
    std::vector<Mm9AnimatedModelAnimationEvent> events;
};

struct Mm9AnimatedModelSkeletonNode
{
    size_t index = 0;
    std::string name;
    int parentIndex = -1;
    uint32_t flags = 0;
    std::vector<size_t> childIndices;
};

struct Mm9AnimatedModelSkeleton
{
    std::vector<Mm9AnimatedModelSkeletonNode> nodes;
};

struct Mm9AnimatedModelSidecar
{
    std::string schema;
    std::string id;
    std::string model;
    std::string sourceFormat;
    std::string sourcePath;
    std::string sourceCommandString;
    int sourceVersion = 0;
    int exportedLodIndex = 0;
    std::vector<float> lodDistances;
    std::vector<Mm9AnimatedModelMaterialRef> materials;
    Mm9AnimatedModelSkeleton skeleton;
    std::vector<AnimatedModelSocket> sockets;
    std::vector<Mm9AnimatedModelAnimationInfo> animations;
};

std::optional<Mm9AnimatedModelSidecar> loadMm9AnimatedModelSidecar(
    const std::filesystem::path &path,
    std::string &errorMessage);

void mergeMm9AnimatedModelSidecar(
    const Mm9AnimatedModelSidecar &sidecar,
    AnimatedModelAsset &asset);
}
