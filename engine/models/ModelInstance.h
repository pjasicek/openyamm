#pragma once

#include "engine/models/ModelAnimation.h"

#include <cstdint>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
struct ModelInstanceHandle
{
    uint32_t index = std::numeric_limits<uint32_t>::max();
    uint32_t generation = 0;

    bool operator==(const ModelInstanceHandle &) const = default;
};

enum class ModelPlaybackMode
{
    Once,
    Loop
};

struct ModelAnimationLayer
{
    uint32_t clipIndex = std::numeric_limits<uint32_t>::max();
    float timeSeconds = 0.0f;
    float weight = 0.0f;
    std::shared_ptr<const std::vector<float>> mask;

    bool operator==(const ModelAnimationLayer &) const = default;
};

class ModelInstanceSystem
{
public:
    ModelInstanceHandle create(std::shared_ptr<const ModelAsset> asset, const ModelTransform &rootTransform = {});
    bool destroy(ModelInstanceHandle handle);
    void clear();

    bool contains(ModelInstanceHandle handle) const;
    bool setTransform(ModelInstanceHandle handle, const ModelTransform &transform);
    bool setVisible(ModelInstanceHandle handle, bool visible);
    bool setMaterialVariant(ModelInstanceHandle handle, uint32_t variant);
    uint32_t materialVariant(ModelInstanceHandle handle) const;
    bool setOutlineColor(ModelInstanceHandle handle, uint32_t colorAbgr);
    uint32_t outlineColor(ModelInstanceHandle handle) const;
    bool setNodeMarkersVisible(ModelInstanceHandle handle, bool visible);
    bool play(ModelInstanceHandle handle, const std::string &clipName, ModelPlaybackMode mode);
    bool pause(ModelInstanceHandle handle, bool paused);
    bool stop(ModelInstanceHandle handle);
    bool setTime(ModelInstanceHandle handle, float timeSeconds);
    bool sample(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds, const ModelTransform &transform);
    bool sampleBlended(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds,
        const ModelTransform &transform, float deltaSeconds, float transitionSeconds,
        const ModelAnimationLayer &layer = {}, bool restart = false);
    void update(float deltaSeconds);

    const ModelAsset *asset(ModelInstanceHandle handle) const;
    std::shared_ptr<const ModelAsset> sharedAsset(ModelInstanceHandle handle) const;
    const ModelPose *pose(ModelInstanceHandle handle, bool deformSkins = true) const;
    const ModelMatrix *nodeMatrix(ModelInstanceHandle handle, uint32_t nodeIndex) const;
    const ModelMatrix *nodeMatrix(ModelInstanceHandle handle, const std::string &nodeName) const;
    const ModelBounds *bounds(ModelInstanceHandle handle) const;
    // Pose bounds of the coarsest LOD mesh: hover/picking precision for a fraction of the skinning work.
    const ModelBounds *pickingBounds(ModelInstanceHandle handle) const;
    const ModelBounds *cullingBounds(ModelInstanceHandle handle) const;
    const ModelBounds *motionBounds(ModelInstanceHandle handle) const;
    float playbackTime(ModelInstanceHandle handle) const;
    bool isPlaying(ModelInstanceHandle handle) const;
    bool isVisible(ModelInstanceHandle handle) const;
    bool areNodeMarkersVisible(ModelInstanceHandle handle) const;
    std::vector<ModelInstanceHandle> handles() const;
    size_t size() const;

private:
    struct Slot
    {
        uint32_t generation = 1;
        bool active = false;
        bool visible = true;
        uint32_t outlineColorAbgr = 0;
        uint32_t materialVariant = 0;
        bool nodeMarkersVisible = false;
        bool playing = false;
        bool paused = false;
        bool clipSelected = false;
        ModelPlaybackMode playbackMode = ModelPlaybackMode::Once;
        uint32_t clipIndex = 0;
        float timeSeconds = 0.0f;
        ModelAnimationLayer layer;
        ModelPose transitionPose;
        float transitionElapsed = 0.0f;
        float transitionDuration = 0.0f;
        mutable ModelPose layerPose;
        ModelTransform rootTransform;
        std::shared_ptr<const ModelAsset> asset;
        std::shared_ptr<const ModelDeformationBounds> deformationBounds;
        mutable ModelPose pose;
        mutable ModelBounds bounds;
        mutable ModelBounds cullingBounds;
        ModelBounds motionBounds;
        mutable bool matricesDirty = true;
        mutable ModelBounds pickingBounds;
        mutable uint64_t pickingBoundsRevision = UINT64_MAX;
        // Clip sampling/blending inputs changed; root-only moves just recompose the hierarchy.
        mutable bool localPoseDirty = true;
        mutable bool verticesDirty = true;
        mutable bool morphVerticesDirty = true;
        mutable bool boundsDirty = true;
    };

    Slot *find(ModelInstanceHandle handle);
    const Slot *find(ModelInstanceHandle handle) const;
    void evaluate(Slot &slot, bool localPoseChanged = true);
    void evaluateMatrices(const Slot &slot) const;

    std::vector<Slot> m_slots;
    std::vector<uint32_t> m_freeIndices;
    size_t m_activeCount = 0;
};
}
