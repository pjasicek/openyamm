#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
struct AnimatedModelVec3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct AnimatedModelQuat
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float w = 1.0f;
};

struct AnimatedModelTransform
{
    AnimatedModelVec3 translation;
    AnimatedModelQuat rotation;
    AnimatedModelVec3 scale = {1.0f, 1.0f, 1.0f};
};

struct AnimatedModelMat4
{
    std::array<float, 16> values = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f};
};

struct AnimatedModelDiagnostic
{
    std::string message;
    bool error = false;
};

struct AnimatedModelVertex
{
    AnimatedModelVec3 position;
    AnimatedModelVec3 normal;
    std::array<float, 2> texcoord = {0.0f, 0.0f};
    std::array<uint32_t, 4> joints = {0, 0, 0, 0};
    std::array<float, 4> weights = {0.0f, 0.0f, 0.0f, 0.0f};
};

struct AnimatedModelBounds
{
    AnimatedModelVec3 min;
    AnimatedModelVec3 max;
    bool valid = false;
};

struct AnimatedModelLodInfo
{
    int exportedIndex = 0;
    std::vector<float> distances;
    bool valid = false;
};

struct AnimatedModelPrimitive
{
    size_t meshIndex = 0;
    size_t primitiveIndex = 0;
    size_t materialIndex = 0;
    size_t vertexCount = 0;
    size_t indexCount = 0;
    bool hasPositions = false;
    bool hasNormals = false;
    bool hasTexcoords = false;
    bool hasJoints = false;
    bool hasWeights = false;
    std::vector<AnimatedModelVertex> vertices;
    std::vector<uint32_t> indices;
    AnimatedModelBounds bounds;
};

struct AnimatedModelMaterial
{
    std::string name;
    std::string baseColorTextureUri;
    bool alphaMask = false;
    bool alphaBlend = false;
    float alphaCutoff = 0.5f;
    bool doubleSided = false;
};

struct AnimatedModelNode
{
    std::string name;
    int parentIndex = -1;
    std::vector<size_t> childIndices;
    AnimatedModelTransform bindTransform;
    bool hasMesh = false;
    std::optional<size_t> skinIndex;
};

struct AnimatedModelJoint
{
    size_t nodeIndex = 0;
    AnimatedModelMat4 inverseBindMatrix;
};

struct AnimatedModelSkin
{
    std::string name;
    std::vector<AnimatedModelJoint> joints;
};

enum class AnimatedModelChannelPath
{
    Translation,
    Rotation,
    Scale,
    Unsupported,
};

struct AnimatedModelChannel
{
    size_t nodeIndex = 0;
    AnimatedModelChannelPath path = AnimatedModelChannelPath::Unsupported;
    std::vector<float> timesSeconds;
    std::vector<AnimatedModelTransform> transforms;
};

struct AnimatedModelEvent
{
    float timeSeconds = 0.0f;
    std::string key;
};

struct AnimatedModelClip
{
    std::string name;
    float durationSeconds = 0.0f;
    std::vector<AnimatedModelChannel> channels;
    std::vector<AnimatedModelEvent> events;
};

struct AnimatedModelController
{
    const AnimatedModelClip *pCurrentClip = nullptr;
    const AnimatedModelClip *pPreviousClip = nullptr;
    float currentTimeSeconds = 0.0f;
    float previousTimeSeconds = 0.0f;
    bool loop = true;
    bool previousLoop = true;
    float rate = 1.0f;
    float transitionDurationSeconds = 0.0f;
    float transitionElapsedSeconds = 0.0f;
};

struct AnimatedModelControllerUpdate
{
    std::vector<AnimatedModelEvent> events;
    bool clipFinished = false;
};

struct AnimatedModelDrawItem
{
    size_t primitiveIndex = 0;
    size_t materialIndex = 0;
    std::vector<AnimatedModelVertex> vertices;
    std::vector<uint32_t> indices;
    std::vector<AnimatedModelMat4> bonePalette;
    std::string texture;
    bool alphaMask = false;
    bool alphaBlend = false;
    bool doubleSided = false;
    AnimatedModelBounds bounds;
};

struct AnimatedModelRenderCounters
{
    size_t skinnedDrawCalls = 0;
    size_t skinnedTriangles = 0;
    size_t uploadedBoneMatrices = 0;
    size_t materialSwitches = 0;
};

struct AnimatedModelRenderPrep
{
    std::vector<AnimatedModelDrawItem> drawItems;
    std::vector<AnimatedModelDiagnostic> diagnostics;
    AnimatedModelRenderCounters counters;
};

struct AnimatedModelSocket
{
    std::string name;
    size_t nodeIndex = 0;
    AnimatedModelTransform localTransform;
};

struct AnimatedModelPose
{
    std::vector<AnimatedModelTransform> localTransforms;
    std::vector<AnimatedModelMat4> globalTransforms;
    std::vector<AnimatedModelMat4> skinningMatrices;
};

struct AnimatedModelAsset
{
    std::string sourceId;
    std::filesystem::path sourcePath;
    std::vector<AnimatedModelNode> nodes;
    std::vector<AnimatedModelPrimitive> primitives;
    std::vector<AnimatedModelMaterial> materials;
    std::vector<AnimatedModelSkin> skins;
    std::vector<AnimatedModelClip> clips;
    std::vector<AnimatedModelSocket> sockets;
    AnimatedModelBounds bounds;
    AnimatedModelLodInfo lod;
    std::vector<AnimatedModelDiagnostic> diagnostics;

    const AnimatedModelClip *findClip(std::string_view name) const;
    std::optional<size_t> findNodeIndex(std::string_view name) const;
    std::optional<size_t> findSocketIndex(std::string_view name) const;
    bool hasErrors() const;
};

std::optional<AnimatedModelAsset> loadAnimatedModelAsset(
    const std::filesystem::path &path,
    std::string &errorMessage);

void validateAnimatedModelAsset(AnimatedModelAsset &asset);

AnimatedModelPose sampleAnimatedModelPose(
    const AnimatedModelAsset &asset,
    const AnimatedModelClip *pClip,
    float timeSeconds,
    bool loop);

std::vector<AnimatedModelEvent> animatedModelEventsInInterval(
    const AnimatedModelClip &clip,
    float startSeconds,
    float endSeconds,
    bool loop);

void animatedModelControllerPlay(
    AnimatedModelController &controller,
    const AnimatedModelClip *pClip,
    bool loop,
    float transitionDurationSeconds);

AnimatedModelControllerUpdate animatedModelControllerUpdate(
    AnimatedModelController &controller,
    float deltaSeconds);

AnimatedModelPose sampleAnimatedModelControllerPose(
    const AnimatedModelAsset &asset,
    const AnimatedModelController &controller);

AnimatedModelRenderPrep buildAnimatedModelRenderPrep(
    const AnimatedModelAsset &asset,
    const AnimatedModelPose &pose,
    size_t maxBoneMatrices);

std::optional<AnimatedModelMat4> animatedModelSocketTransform(
    const AnimatedModelAsset &asset,
    const AnimatedModelPose &pose,
    std::string_view socketName);

bool animatedModelMatrixIsFinite(const AnimatedModelMat4 &matrix);
}
