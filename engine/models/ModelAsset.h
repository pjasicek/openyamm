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
    // PNG, or a cooked block-compressed texture (.oytex, engine/render/CookedTexture.h) referenced by URI.
    std::vector<uint8_t> bytes;
    bool cooked = false;
};

// glTF sampler values; zero filter values request the renderer's linear mip filtering default.
struct ModelSampler
{
    int minFilter = 0;
    int magFilter = 0;
    int wrapS = 10497;
    int wrapT = 10497;
};

constexpr size_t ModelColorRampStops = 16;
constexpr size_t ModelMaxColorRegions = 4;

struct ModelColorRamp
{
    std::array<float, 2> luminanceRange = {0.0f, 1.0f};
    std::array<std::array<float, 3>, ModelColorRampStops> colors = {};
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
    // Colour variants of one shared skin (glTF material extras). "openyamm_region_mask" names a texture whose R, G, B
    // and A channels mark up to four regions; "openyamm_region_ramps" gives each region, in channel order, a linear
    // luminance range and a linear-RGB ramp. Inside a region the base colour becomes the ramp colour at its
    // normalised luminance, so tier variants share every image and differ only in their ramps.
    int regionMaskImageIndex = -1;
    ModelSampler regionMaskSampler;
    std::vector<ModelColorRamp> regionRamps;
    // Static decoration extras: "openyamm_wind" sways the vertex by up to this many model units at the model's top,
    // growing with (height / model height)^2; "openyamm_billboard" turns the mesh (a quad in the model's x/up plane)
    // about the vertical axis to face the camera, as a far impostor.
    float wind = 0.0f;
    bool billboard = false;
    // "openyamm_translucency": sunlight passing through thin leaves (0..1).
    float translucency = 0.0f;
    // "openyamm_specular": scale of sun, point-light and sky specular (0..1); foliage cards use a small value.
    float specular = 1.0f;
    // "openyamm_specular_mask": the metallic-roughness texture's red channel (unused by glTF) scales specular per
    // texel, so a matte head and glossy armour can share one material and one draw.
    bool specularMask = false;
    // Texture animation of static decorations. "openyamm_uv_scroll": [du, dv] texture units per second (flowing water);
    // "openyamm_flipbook": [columns, rows, frames per second], frames left to right then top to bottom, looping with a
    // per-placement phase (fire). "openyamm_flutter": cloth wave amplitude in model units; each vertex moves along
    // its normal by amplitude x COLOR_0 alpha x a wave travelling along texture coordinate u (flags).
    // "openyamm_pulse": [amplitude, period seconds]; the emission is scaled by 1 + amplitude x sin(2 pi t / period),
    // with the per-placement phase (glowing crystals).
    std::array<float, 2> uvScroll = {};
    std::array<float, 3> flipbook = {};
    float flutter = 0.0f;
    std::array<float, 2> pulse = {};
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
    // glTF COLOR_0 (linear RGBA, multiplies the base colour); empty when absent. Drawn by static placements.
    std::vector<std::array<uint8_t, 4>> colors;
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
