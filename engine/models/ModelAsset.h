#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
using ModelMatrix = std::array<float, 16>;

struct ModelTransform
{
    std::array<float, 3> translation = {0.0f, 0.0f, 0.0f};
    std::array<float, 4> rotation = {0.0f, 0.0f, 0.0f, 1.0f};
    std::array<float, 3> scale = {1.0f, 1.0f, 1.0f};
    bool operator==(const ModelTransform &) const = default;
};

struct ModelVertex
{
    std::array<float, 3> position = {};
    std::array<float, 3> normal = {};
    std::array<float, 2> texCoord = {};
};

enum class ModelAlphaMode
{
    Opaque,
    Mask,
    Blend
};

struct ModelImage
{
    std::string name;
    std::string sourcePath;
    std::vector<uint8_t> pngBytes;
};

// glTF sampler values; zero filter values request the renderer's linear mip filtering default.
struct ModelSampler
{
    int minFilter = 0;
    int magFilter = 0;
    int wrapS = 10497;
    int wrapT = 10497;
};

struct ModelMaterial
{
    std::string name;
    std::array<float, 4> baseColor = {1.0f, 1.0f, 1.0f, 1.0f};
    int imageIndex = -1;
    int normalImageIndex = -1;
    int metallicRoughnessImageIndex = -1;
    float metallic = 1.0f;
    float roughness = 1.0f;
    ModelSampler baseSampler;
    ModelSampler normalSampler;
    ModelSampler metallicRoughnessSampler;
    float normalScale = 1.0f;
    std::array<float, 3> emissive = {};
    ModelAlphaMode alphaMode = ModelAlphaMode::Opaque;
    float alphaCutoff = 0.5f;
    bool doubleSided = false;
    bool unlit = false;
};

struct ModelVertexInfluences
{
    std::array<uint16_t, 8> joints = {};
    std::array<float, 8> weights = {};
};

struct ModelMorphTarget
{
    std::vector<std::array<float, 3>> positions;
    std::vector<std::array<float, 3>> normals;
};

struct ModelPrimitive
{
    std::vector<ModelVertex> vertices;
    std::vector<uint32_t> indices;
    // Default material first, followed by KHR_materials_variants in asset order.
    std::vector<int> materialIndices = {-1};
    std::vector<ModelVertexInfluences> influences;
    std::vector<ModelMorphTarget> morphTargets;
};

struct ModelMesh
{
    std::string name;
    std::vector<ModelPrimitive> primitives;
    std::vector<float> weights;
    // Lower colour meshes; shadow meshes include their own level zero. All share the node's rig.
    std::vector<uint32_t> lodMeshes;
    std::vector<uint32_t> shadowMeshes;
};

struct ModelSkin
{
    std::vector<uint32_t> joints;
    std::vector<ModelMatrix> inverseBindMatrices;
};

struct ModelNode
{
    std::string name;
    int parentIndex = -1;
    std::vector<uint32_t> childIndices;
    int meshIndex = -1;
    int skinIndex = -1;
    std::vector<float> weights;
    bool usesMatrix = false;
    ModelTransform transform;
    ModelMatrix matrix = {};
};

enum class ModelAnimationInterpolation
{
    Step,
    Linear
};

enum class ModelAnimationTarget
{
    Translation,
    Rotation,
    Scale,
    Weights
};

struct ModelAnimationChannel
{
    uint32_t nodeIndex = 0;
    ModelAnimationTarget target = ModelAnimationTarget::Translation;
    ModelAnimationInterpolation interpolation = ModelAnimationInterpolation::Linear;
    std::vector<float> times;
    std::vector<std::array<float, 4>> values;
    std::vector<std::vector<float>> weightValues;
};

struct ModelAnimationClip
{
    std::string name;
    float durationSeconds = 0.0f;
    std::vector<ModelAnimationChannel> channels;
};

struct ModelBounds
{
    std::array<float, 3> min = {};
    std::array<float, 3> max = {};
    bool valid = false;
};

struct ModelAsset
{
    std::string sourcePath;
    std::vector<ModelImage> images;
    std::vector<ModelMaterial> materials;
    std::vector<ModelMesh> meshes;
    std::vector<ModelNode> nodes;
    std::vector<ModelSkin> skins;
    std::vector<uint32_t> hierarchyOrder;
    std::vector<ModelAnimationClip> clips;
    std::unordered_map<std::string, uint32_t> nodeIndicesByName;
    std::unordered_map<std::string, uint32_t> clipIndicesByName;
    std::vector<std::string> materialVariants;
    ModelBounds staticBounds;

    std::optional<uint32_t> findNode(const std::string &name) const;
    std::optional<uint32_t> findClip(const std::string &name) const;
    std::optional<uint32_t> findMaterialVariant(const std::string &name) const;
};

float determinant3x3(const ModelMatrix &matrix);
ModelMatrix modelNormalMatrix(const ModelMatrix &matrix);
bool modelMatrixVisible(const ModelMatrix &matrix);

ModelMatrix identityModelMatrix();
ModelMatrix composeModelTransform(const ModelTransform &transform);
ModelMatrix multiplyModelMatrices(const ModelMatrix &left, const ModelMatrix &right);
ModelTransform gltfModelPlacement(
    const std::array<float, 3> &openYammPosition,
    float yawRadians = 0.0f,
    float uniformScale = 1.0f);
ModelTransform gltfModelPlacement(
    const std::array<float, 3> &openYammPosition,
    const std::array<float, 4> &openYammRotation,
    float uniformScale = 1.0f);
}
