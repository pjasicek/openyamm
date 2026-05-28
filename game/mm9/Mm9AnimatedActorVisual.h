#pragma once

#include "game/mm9/Mm9AnimatedModelResolver.h"
#include "game/render/AnimatedModelAsset.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9AnimatedActorVisualSource
{
    std::string mapId;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string sourceSkin;
    std::string requestedClip;
    std::string semanticState = "idle";
    bool visible = true;
    bool solid = true;
    bool rayHit = true;
    bool pickable = true;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float facingRadians = 0.0f;
    float scale = 1.0f;
    float radius = 32.0f;
    float height = 128.0f;
    float verticalOffset = 0.0f;
    size_t maxBoneMatrices = 128;
};

struct Mm9AnimatedActorSocketCacheEntry
{
    std::string name;
    AnimatedModelMat4 modelTransform;
    AnimatedModelMat4 worldTransform;
};

struct Mm9AnimatedActorVisual
{
    std::string mapId;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string sourceSkin;
    std::string modelId;
    std::string skinBindingId;
    std::filesystem::path modelAssetPath;
    std::filesystem::path modelSidecarPath;
    std::vector<Mm9AnimatedModelMaterialOverride> materialOverrides;
    std::string currentClipName;
    std::string semanticState;
    AnimatedModelController controller;
    AnimatedModelPose poseCache;
    AnimatedModelRenderPrep renderPrepCache;
    std::vector<Mm9AnimatedActorSocketCacheEntry> socketCache;
    AnimatedModelMat4 modelToWorld;
    AnimatedModelBounds worldBounds;
    bool visible = true;
    bool solid = true;
    bool rayHit = true;
    bool pickable = true;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float facingRadians = 0.0f;
    float scale = 1.0f;
    float radius = 32.0f;
    float height = 128.0f;
    float verticalOffset = 0.0f;
    size_t maxBoneMatrices = 128;
    std::vector<AnimatedModelDiagnostic> diagnostics;
};

struct Mm9AnimatedActorVisualUpdate
{
    std::vector<AnimatedModelEvent> events;
    bool clipFinished = false;
};

const AnimatedModelClip *resolveMm9AnimatedActorClip(
    const AnimatedModelAsset &asset,
    const std::string &requestedClip,
    const std::string &semanticState,
    std::vector<AnimatedModelDiagnostic> &diagnostics);

bool initializeMm9AnimatedActorVisual(
    const Mm9AnimatedActorVisualSource &source,
    const Mm9AnimatedModelResolution &resolution,
    const AnimatedModelAsset &asset,
    Mm9AnimatedActorVisual &visual);

bool setMm9AnimatedActorVisualClip(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    const std::string &requestedClip,
    const std::string &semanticState,
    bool loop,
    float transitionSeconds);

void setMm9AnimatedActorVisualTransform(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    float x,
    float y,
    float z,
    float facingRadians,
    float scale);

Mm9AnimatedActorVisualUpdate updateMm9AnimatedActorVisual(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    float deltaSeconds);

std::optional<AnimatedModelMat4> findMm9AnimatedActorSocketTransform(
    const Mm9AnimatedActorVisual &visual,
    const std::string &socketName);

std::optional<AnimatedModelMat4> findMm9AnimatedActorWorldSocketTransform(
    const Mm9AnimatedActorVisual &visual,
    const std::string &socketName);
}
