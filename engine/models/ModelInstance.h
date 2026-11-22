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

// A rigid model carried on one node of an instance, such as a staff on its hand bone. Its mesh is in that node's space
// (tools/split_attachment.py), so it is drawn with the node's world matrix; renderers draw it as a static placement
// lit like its owner, instanced with every other carrier of the same model.
struct ModelAttachment
{
    std::shared_ptr<const ModelAsset> asset;
    uint32_t nodeIndex = 0;
    uint32_t materialVariant = 0;
    // Places the asset in the node's space when it was not authored there (a ground item model held in a hand,
    // game/render/HeldWeapons.h); none: the asset is already in the node's space.
    std::optional<ModelMatrix> localMatrix;

    // The node's matrix with the local placement applied.
    ModelMatrix placed(const ModelMatrix &nodeMatrix) const
    {
        return localMatrix ? multiplyModelMatrices(nodeMatrix, *localMatrix) : nodeMatrix;
    }
};

// A world-space rotation applied after the clip about one node's pivot, carrying the node's subtree (a head turned
// toward a target over its animated pose). Rotations apply in list order, so a chain is listed root to tip.
struct ModelNodeRotation
{
    uint32_t nodeIndex = 0;
    std::array<float, 4> rotation = {0.0f, 0.0f, 0.0f, 1.0f};

    bool operator==(const ModelNodeRotation &) const = default;
};

// A burn consuming an instance's skinned surface (actors.yml death_effect: burn). Each material's burn map
// (ModelMaterial::burnMapImageIndex) orders its texels from 0 to 1, and `front` sweeps that order. Texels within
// charWidth ahead of the front char; behind it a glowing edge edgeWidth wide still stands, then the surface is gone
// and, for fireWidth more, burns on as additive fire in its place, so the burnt body briefly remains a silhouette of
// flame. Skinned draws only; the burn is over once the front passes 1 + edgeWidth + fireWidth.
struct ModelBurn
{
    float front = 0.0f;
    float charWidth = 0.12f;
    float edgeWidth = 0.03f;
    float fireWidth = 0.0f;
    // Linear RGB of the edge and fire emission, brightness included.
    std::array<float, 3> color = {};
    // Clock of the fire's flicker, in seconds.
    float seconds = 0.0f;
};

// An energy shield drawn over an instance's skinned surface (game: GameplayActorShields): a translucent fresnel shell
// pushed out along the normals, additive, with ripples at recent hits, a rise from the feet when it comes up and a
// shatter when it breaks. Skinned and CPU-deformed draws only; null draws nothing (no cost).
struct ModelShieldShell
{
    static constexpr size_t MaxHits = 4;

    // Linear RGB and overall strength (0 draws nothing).
    std::array<float, 3> color = {1.0f, 0.4f, 0.8f};
    float strength = 1.0f;
    // Share of the pool left (weaker shells flicker).
    float fraction = 1.0f;
    // Seconds since it broke (shatter, about 0.7 s) or came back up (rise, about 0.5 s); -1 for none.
    float breakSeconds = -1.0f;
    float raiseSeconds = -1.0f;
    // Clock of the drifting energy, in seconds.
    float seconds = 0.0f;
    // World height of the feet and body height, for the rise sweep; offset of the shell from the skin.
    float footZ = 0.0f;
    float bodyHeight = 100.0f;
    float thickness = 3.0f;
    // World impact point and age in seconds of recent hits (age < 0: unused).
    std::array<std::array<float, 4>, MaxHits> hits = {};
};

inline bool modelBurnConsumed(const ModelBurn &burn)
{
    return burn.front > 1.0f + burn.edgeWidth + burn.fireWidth;
}

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
    // Fraction of a flash colour mixed over the instance's skinned draws (a creature hit), 0 = none.
    bool setHitFlash(ModelInstanceHandle handle, float amount);
    float hitFlash(ModelInstanceHandle handle) const;
    // Multiplier of the emission of the instance's skinned draws (a creature's frenzy glow), 1 = as authored.
    bool setEmissionMultiplier(ModelInstanceHandle handle, float multiplier);
    float emissionMultiplier(ModelInstanceHandle handle) const;
    // A display colour (0 to 1) every colour region of the instance's skinned draws is turned to
    // (recoloredModelRamp): one more colour variant of a skin, made of the variant it shows. Materials without
    // colour regions stay as they are. Null draws the variant's own colours.
    bool setRegionRecolor(ModelInstanceHandle handle, const std::array<float, 3> *pSrgbColor);
    const std::array<float, 3> *regionRecolor(ModelInstanceHandle handle) const;
    // Null stops the burn: the surface is whole again.
    bool setBurn(ModelInstanceHandle handle, const ModelBurn *pBurn);
    const ModelBurn *burn(ModelInstanceHandle handle) const;
    // Null removes the shield shell.
    bool setShieldShell(ModelInstanceHandle handle, const ModelShieldShell *pShell);
    const ModelShieldShell *shieldShell(ModelInstanceHandle handle) const;
    bool setNodeMarkersVisible(ModelInstanceHandle handle, bool visible);
    bool setAttachments(ModelInstanceHandle handle, std::vector<ModelAttachment> attachments);
    bool setNodeRotations(ModelInstanceHandle handle, std::vector<ModelNodeRotation> rotations);
    const std::vector<ModelAttachment> &attachments(ModelInstanceHandle handle) const;
    // A static stand-in replaces the instance's own skinned draws: renderers draw this unskinned asset (same material
    // variants) as a static placement at the instance's root transform. Used for corpses, whose pose is frozen
    // (bakeStaticModelPose). The instance keeps its pose, bounds, attachments and picking. Null restores normal draws.
    // minimumPixels: the stand-in is not drawn where it would be smaller on screen than this (ground items far away);
    // 0 draws it at every size.
    bool setStaticStandIn(ModelInstanceHandle handle, std::shared_ptr<const ModelAsset> asset,
        float minimumPixels = 0.0f);
    const std::shared_ptr<const ModelAsset> &staticStandIn(ModelInstanceHandle handle) const;
    float staticStandInMinimumPixels(ModelInstanceHandle handle) const;
    // Fraction of the static stand-in's and attachments' pixels drawn (screen-door dissolve, 1 = solid, 0 = hidden);
    // skinned draws ignore it.
    bool setCoverage(ModelInstanceHandle handle, float coverage);
    float coverage(ModelInstanceHandle handle) const;
    // Changes whenever a static stand-in is added, removed, moved, shown or hidden, or restyled, so renderers can keep
    // their placements between frames.
    uint64_t standInRevision() const
    {
        return m_standInRevision;
    }
    const ModelTransform *rootTransform(ModelInstanceHandle handle) const;
    bool play(ModelInstanceHandle handle, const std::string &clipName, ModelPlaybackMode mode);
    bool pause(ModelInstanceHandle handle, bool paused);
    bool stop(ModelInstanceHandle handle);
    bool setTime(ModelInstanceHandle handle, float timeSeconds);
    bool sample(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds, const ModelTransform &transform);
    // blendStepSeconds: a transition's progress moves in steps of this length (the caller's animation rate, as its
    // clip times), so a blending pose is not sampled again every frame; 0 moves it every frame.
    bool sampleBlended(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds,
        const ModelTransform &transform, float deltaSeconds, float transitionSeconds,
        const ModelAnimationLayer &layer = {}, bool restart = false, float blendStepSeconds = 0.0f);
    void update(float deltaSeconds);

    const ModelAsset *asset(ModelInstanceHandle handle) const;
    std::shared_ptr<const ModelAsset> sharedAsset(ModelInstanceHandle handle) const;
    const ModelPose *pose(ModelInstanceHandle handle, bool deformSkins = true) const;
    const ModelMatrix *nodeMatrix(ModelInstanceHandle handle, uint32_t nodeIndex) const;
    const ModelMatrix *nodeMatrix(ModelInstanceHandle handle, const std::string &nodeName) const;
    const ModelBounds *bounds(ModelInstanceHandle handle) const;
    // Pose bounds of the coarsest LOD mesh: hover/picking precision for a fraction of the skinning work.
    // Once burnt out, only visible rigid attachments remain pickable.
    const ModelBounds *pickingBounds(ModelInstanceHandle handle) const;
    // Distance along direction to where the ray meets the posed coarsest LOD triangles (once burnt out, the
    // pickingBounds box); none on a miss. Callers test the cheaper bounds first.
    std::optional<float> pickRay(ModelInstanceHandle handle, const std::array<float, 3> &origin,
        const std::array<float, 3> &direction) const;
    const ModelBounds *cullingBounds(ModelInstanceHandle handle) const;
    const ModelBounds *motionBounds(ModelInstanceHandle handle) const;
    // Bind-space bounds of each skin joint's vertices (shared by every instance of the asset), behind cullingBounds.
    const ModelDeformationBounds *deformationBounds(ModelInstanceHandle handle) const;
    float playbackTime(ModelInstanceHandle handle) const;
    // Clip and upper-body layer last selected by sample/sampleBlended (UINT32_MAX / an empty layer without one).
    uint32_t sampledClip(ModelInstanceHandle handle) const;
    const ModelAnimationLayer *sampledLayer(ModelInstanceHandle handle) const;
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
        float hitFlash = 0.0f;
        float emissionMultiplier = 1.0f;
        std::optional<std::array<float, 3>> regionRecolor;
        std::optional<ModelBurn> burn;
        std::optional<ModelShieldShell> shieldShell;
        uint32_t materialVariant = 0;
        bool nodeMarkersVisible = false;
        std::vector<ModelAttachment> attachments;
        std::vector<ModelNodeRotation> nodeRotations;
        mutable std::vector<uint8_t> rotatedNodes;
        std::shared_ptr<const ModelAsset> staticStandIn;
        float standInMinimumPixels = 0.0f;
        float coverage = 1.0f;
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
        // The transition progress of the evaluated pose (transitionElapsed in blend steps).
        float transitionShown = 0.0f;
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
        // The triangles behind pickingBounds; empty once burnt out.
        mutable ModelPoseGeometry pickingGeometry;
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
    void standInChanged(const Slot &slot);
    // Revisions are unique across all instance systems, so a renderer's cached revision never matches another system.
    static uint64_t nextStandInRevision();

    std::vector<Slot> m_slots;
    std::vector<uint32_t> m_freeIndices;
    size_t m_activeCount = 0;
    uint64_t m_standInRevision = nextStandInRevision();
};
}
