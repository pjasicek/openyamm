#include "game/mm9/Mm9AnimatedActorVisual.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
std::string lowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(
        output.begin(),
        output.end(),
        output.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return output;
}

void addDiagnostic(
    std::vector<AnimatedModelDiagnostic> &diagnostics,
    const std::string &message,
    bool error)
{
    diagnostics.push_back(AnimatedModelDiagnostic{
        .message = message,
        .error = error,
    });
}

std::vector<std::string> fallbackClipNames(const std::string &semanticState)
{
    const std::string semantic = lowerCopy(semanticState);
    if (semantic == "idle" || semantic == "stand" || semantic == "stationary")
    {
        return {"idle", "stand", "stand1", "standAir", "standwater", "static_model"};
    }
    if (semantic == "walk" || semantic == "walking")
    {
        return {"walk", "walk3", "swim", "run", "fly", "stand", "stand1", "standwater", "idle"};
    }
    if (semantic == "run" || semantic == "running")
    {
        return {"run", "run2", "walk", "walk3", "swim", "fly", "stand", "stand1", "standwater", "idle"};
    }
    if (semantic == "fly" || semantic == "flying")
    {
        return {"fly", "Fly", "standAir", "run", "walk", "stand", "idle"};
    }
    if (semantic == "melee" || semantic == "attack" || semantic == "melee_attack")
    {
        return {"Hattack1", "Hattack2", "hattackwater1", "Lattack", "Rattack", "attack", "stand", "idle"};
    }
    if (semantic == "range" || semantic == "ranged" || semantic == "ranged_attack")
    {
        return {"Rattack1", "RattackAir1", "rangeAttack", "attack", "stand", "idle"};
    }
    if (semantic == "pain" || semantic == "wince" || semantic == "hit")
    {
        return {"wince1", "wince2", "wincewater1", "pain", "stand", "idle"};
    }
    if (semantic == "death" || semantic == "dead")
    {
        return {"death", "Death", "dead", "die1", "stand", "stand1", "idle"};
    }
    return {"stand", "stand1", "standwater", "idle", "static_model"};
}

bool clipLoopsForSemantic(const std::string &semanticState)
{
    const std::string semantic = lowerCopy(semanticState);
    return semantic == "idle" || semantic == "stand" || semantic == "stationary"
        || semantic == "walk" || semantic == "walking"
        || semantic == "run" || semantic == "running"
        || semantic == "fly" || semantic == "flying";
}

const Mm9AnimatedModelMaterialOverride *findMaterialOverride(
    const Mm9AnimatedActorVisual &visual,
    size_t materialIndex)
{
    for (const Mm9AnimatedModelMaterialOverride &materialOverride : visual.materialOverrides)
    {
        if (materialOverride.materialIndex == materialIndex)
        {
            return &materialOverride;
        }
    }
    return nullptr;
}

AnimatedModelMat4 multiplyMatrix(const AnimatedModelMat4 &a, const AnimatedModelMat4 &b)
{
    AnimatedModelMat4 result = {};
    result.values.fill(0.0f);

    for (size_t column = 0; column < 4; ++column)
    {
        for (size_t row = 0; row < 4; ++row)
        {
            for (size_t index = 0; index < 4; ++index)
            {
                result.values[column * 4 + row] +=
                    a.values[index * 4 + row] * b.values[column * 4 + index];
            }
        }
    }

    return result;
}

AnimatedModelMat4 actorModelToWorldMatrix(
    float x,
    float y,
    float z,
    float facingRadians,
    float scale)
{
    const float cosine = std::cos(facingRadians);
    const float sine = std::sin(facingRadians);

    AnimatedModelMat4 matrix = {};
    matrix.values[0] = cosine * scale;
    matrix.values[1] = sine * scale;
    matrix.values[4] = -sine * scale;
    matrix.values[5] = cosine * scale;
    matrix.values[10] = scale;
    matrix.values[12] = x;
    matrix.values[13] = y;
    matrix.values[14] = z;
    return matrix;
}

AnimatedModelVec3 transformPoint(const AnimatedModelMat4 &matrix, const AnimatedModelVec3 &point)
{
    return {
        matrix.values[0] * point.x + matrix.values[4] * point.y
            + matrix.values[8] * point.z + matrix.values[12],
        matrix.values[1] * point.x + matrix.values[5] * point.y
            + matrix.values[9] * point.z + matrix.values[13],
        matrix.values[2] * point.x + matrix.values[6] * point.y
            + matrix.values[10] * point.z + matrix.values[14]};
}

void expandBounds(AnimatedModelBounds &bounds, const AnimatedModelVec3 &point)
{
    if (!bounds.valid)
    {
        bounds.min = point;
        bounds.max = point;
        bounds.valid = true;
        return;
    }

    bounds.min.x = std::min(bounds.min.x, point.x);
    bounds.min.y = std::min(bounds.min.y, point.y);
    bounds.min.z = std::min(bounds.min.z, point.z);
    bounds.max.x = std::max(bounds.max.x, point.x);
    bounds.max.y = std::max(bounds.max.y, point.y);
    bounds.max.z = std::max(bounds.max.z, point.z);
}

AnimatedModelBounds transformBounds(
    const AnimatedModelMat4 &matrix,
    const AnimatedModelBounds &bounds)
{
    AnimatedModelBounds result = {};
    if (!bounds.valid)
    {
        return result;
    }

    const float xs[2] = {bounds.min.x, bounds.max.x};
    const float ys[2] = {bounds.min.y, bounds.max.y};
    const float zs[2] = {bounds.min.z, bounds.max.z};
    for (const float x : xs)
    {
        for (const float y : ys)
        {
            for (const float z : zs)
            {
                expandBounds(result, transformPoint(matrix, {x, y, z}));
            }
        }
    }
    return result;
}

void refreshTransformCache(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset)
{
    visual.modelToWorld = actorModelToWorldMatrix(
        visual.x,
        visual.y,
        visual.z,
        visual.facingRadians,
        visual.scale);
    visual.worldBounds = transformBounds(visual.modelToWorld, asset.bounds);
}

void refreshSocketCache(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset)
{
    visual.socketCache.clear();
    visual.socketCache.reserve(asset.sockets.size());
    for (const AnimatedModelSocket &socket : asset.sockets)
    {
        const std::optional<AnimatedModelMat4> transform =
            animatedModelSocketTransform(asset, visual.poseCache, socket.name);
        if (transform.has_value())
        {
            visual.socketCache.push_back(Mm9AnimatedActorSocketCacheEntry{
                .name = socket.name,
                .modelTransform = *transform,
                .worldTransform = multiplyMatrix(visual.modelToWorld, *transform),
            });
        }
    }
}

void refreshRenderPrepCache(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset)
{
    visual.renderPrepCache = buildAnimatedModelRenderPrep(asset, visual.poseCache, visual.maxBoneMatrices);
    for (AnimatedModelDrawItem &drawItem : visual.renderPrepCache.drawItems)
    {
        const Mm9AnimatedModelMaterialOverride *pOverride =
            findMaterialOverride(visual, drawItem.materialIndex);
        if (pOverride != nullptr)
        {
            drawItem.texture = pOverride->runtimeTexture;
        }
    }
}
}

const AnimatedModelClip *resolveMm9AnimatedActorClip(
    const AnimatedModelAsset &asset,
    const std::string &requestedClip,
    const std::string &semanticState,
    std::vector<AnimatedModelDiagnostic> &diagnostics)
{
    if (!requestedClip.empty())
    {
        const AnimatedModelClip *pClip = asset.findClip(requestedClip);
        if (pClip != nullptr)
        {
            return pClip;
        }

        addDiagnostic(
            diagnostics,
            "MM9 animated actor requested clip is missing: " + requestedClip,
            false);
    }

    for (const std::string &clipName : fallbackClipNames(semanticState))
    {
        const AnimatedModelClip *pClip = asset.findClip(clipName);
        if (pClip != nullptr)
        {
            return pClip;
        }
    }

    if (asset.clips.size() == 1)
    {
        addDiagnostic(
            diagnostics,
            "MM9 animated actor using only available source clip for semantic state: " + semanticState,
            false);
        return &asset.clips.front();
    }

    addDiagnostic(
        diagnostics,
        "MM9 animated actor has no clip for semantic state: " + semanticState,
        true);
    return nullptr;
}

bool initializeMm9AnimatedActorVisual(
    const Mm9AnimatedActorVisualSource &source,
    const Mm9AnimatedModelResolution &resolution,
    const AnimatedModelAsset &asset,
    Mm9AnimatedActorVisual &visual)
{
    visual = {};
    visual.mapId = source.mapId;
    visual.objectId = source.objectId;
    visual.sourceObjectIndex = source.sourceObjectIndex;
    visual.sourceClass = source.sourceClass;
    visual.sourceName = source.sourceName;
    visual.sourceModel = source.sourceModel;
    visual.sourceSkin = source.sourceSkin;
    visual.modelId = resolution.modelId;
    visual.skinBindingId = resolution.skinBindingId;
    visual.modelAssetPath = resolution.modelAssetPath;
    visual.modelSidecarPath = resolution.modelSidecarPath;
    visual.materialOverrides = resolution.materialOverrides;
    visual.visible = source.visible;
    visual.solid = source.solid;
    visual.rayHit = source.rayHit;
    visual.pickable = source.pickable;
    visual.x = source.x;
    visual.y = source.y;
    visual.z = source.z;
    visual.facingRadians = source.facingRadians;
    visual.scale = source.scale;
    visual.radius = source.radius;
    visual.height = source.height;
    visual.verticalOffset = source.verticalOffset;
    visual.maxBoneMatrices = source.maxBoneMatrices;
    refreshTransformCache(visual, asset);

    const bool loop = clipLoopsForSemantic(source.semanticState);
    return setMm9AnimatedActorVisualClip(
        visual,
        asset,
        source.requestedClip,
        source.semanticState,
        loop,
        0.0f);
}

bool setMm9AnimatedActorVisualClip(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    const std::string &requestedClip,
    const std::string &semanticState,
    bool loop,
    float transitionSeconds)
{
    visual.semanticState = semanticState;
    const AnimatedModelClip *pClip = resolveMm9AnimatedActorClip(
        asset,
        requestedClip,
        semanticState,
        visual.diagnostics);
    if (pClip == nullptr)
    {
        visual.currentClipName.clear();
        visual.poseCache = sampleAnimatedModelPose(asset, nullptr, 0.0f, true);
        refreshRenderPrepCache(visual, asset);
        refreshSocketCache(visual, asset);
        return false;
    }

    visual.currentClipName = pClip->name;
    animatedModelControllerPlay(visual.controller, pClip, loop, transitionSeconds);
    visual.poseCache = sampleAnimatedModelControllerPose(asset, visual.controller);
    refreshRenderPrepCache(visual, asset);
    refreshSocketCache(visual, asset);
    return true;
}

void setMm9AnimatedActorVisualTransform(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    float x,
    float y,
    float z,
    float facingRadians,
    float scale)
{
    visual.x = x;
    visual.y = y;
    visual.z = z;
    visual.facingRadians = facingRadians;
    visual.scale = scale;
    refreshTransformCache(visual, asset);
    refreshSocketCache(visual, asset);
}

Mm9AnimatedActorVisualUpdate updateMm9AnimatedActorVisual(
    Mm9AnimatedActorVisual &visual,
    const AnimatedModelAsset &asset,
    float deltaSeconds)
{
    const AnimatedModelControllerUpdate controllerUpdate =
        animatedModelControllerUpdate(visual.controller, deltaSeconds);
    visual.poseCache = sampleAnimatedModelControllerPose(asset, visual.controller);
    refreshRenderPrepCache(visual, asset);
    refreshSocketCache(visual, asset);

    return Mm9AnimatedActorVisualUpdate{
        .events = controllerUpdate.events,
        .clipFinished = controllerUpdate.clipFinished,
    };
}

std::optional<AnimatedModelMat4> findMm9AnimatedActorSocketTransform(
    const Mm9AnimatedActorVisual &visual,
    const std::string &socketName)
{
    const std::string socketKey = lowerCopy(socketName);
    for (const Mm9AnimatedActorSocketCacheEntry &entry : visual.socketCache)
    {
        if (lowerCopy(entry.name) == socketKey)
        {
            return entry.modelTransform;
        }
    }
    return std::nullopt;
}

std::optional<AnimatedModelMat4> findMm9AnimatedActorWorldSocketTransform(
    const Mm9AnimatedActorVisual &visual,
    const std::string &socketName)
{
    const std::string socketKey = lowerCopy(socketName);
    for (const Mm9AnimatedActorSocketCacheEntry &entry : visual.socketCache)
    {
        if (lowerCopy(entry.name) == socketKey)
        {
            return entry.worldTransform;
        }
    }
    return std::nullopt;
}
}
