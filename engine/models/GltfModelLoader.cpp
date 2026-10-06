#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelAnimation.h"

#include "engine/AssetFileSystem.h"

#include <cgltf/cgltf.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <limits>
#include <memory>
#include <string_view>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
struct CgltfDeleter
{
    void operator()(cgltf_data *pData) const
    {
        cgltf_free(pData);
    }
};

struct AssetFileContext
{
    const AssetFileSystem *pAssetFileSystem = nullptr;
};

void *cgltfAllocate(const cgltf_memory_options *pMemoryOptions, size_t size)
{
    if (pMemoryOptions->alloc_func != nullptr)
    {
        return pMemoryOptions->alloc_func(pMemoryOptions->user_data, size);
    }
    return std::malloc(size);
}

void cgltfReleaseMemory(const cgltf_memory_options *pMemoryOptions, void *pData)
{
    if (pMemoryOptions->free_func != nullptr)
    {
        pMemoryOptions->free_func(pMemoryOptions->user_data, pData);
        return;
    }
    std::free(pData);
}

cgltf_result readAssetFile(
    const cgltf_memory_options *pMemoryOptions,
    const cgltf_file_options *pFileOptions,
    const char *pPath,
    cgltf_size *pSize,
    void **ppData
)
{
    const AssetFileContext *pContext = static_cast<const AssetFileContext *>(pFileOptions->user_data);
    const std::optional<std::vector<uint8_t>> bytes = pContext->pAssetFileSystem->readBinaryFile(pPath);
    if (!bytes)
    {
        return cgltf_result_file_not_found;
    }
    if (pSize != nullptr && *pSize != 0 && bytes->size() < *pSize)
    {
        return cgltf_result_data_too_short;
    }

    void *pCopy = cgltfAllocate(pMemoryOptions, bytes->size());
    if (pCopy == nullptr && !bytes->empty())
    {
        return cgltf_result_out_of_memory;
    }
    if (!bytes->empty())
    {
        std::memcpy(pCopy, bytes->data(), bytes->size());
    }
    if (pSize != nullptr)
    {
        *pSize = bytes->size();
    }
    *ppData = pCopy;
    return cgltf_result_success;
}

void releaseAssetFile(
    const cgltf_memory_options *pMemoryOptions,
    const cgltf_file_options *,
    void *pData,
    cgltf_size
)
{
    cgltfReleaseMemory(pMemoryOptions, pData);
}

std::string cgltfResultName(cgltf_result result)
{
    switch (result)
    {
    case cgltf_result_success:
        return "success";
    case cgltf_result_data_too_short:
        return "data is truncated";
    case cgltf_result_unknown_format:
        return "unknown format";
    case cgltf_result_invalid_json:
        return "invalid JSON";
    case cgltf_result_invalid_gltf:
        return "invalid glTF";
    case cgltf_result_invalid_options:
        return "invalid loader options";
    case cgltf_result_file_not_found:
        return "referenced file was not found";
    case cgltf_result_io_error:
        return "I/O error";
    case cgltf_result_out_of_memory:
        return "out of memory";
    case cgltf_result_legacy_gltf:
        return "legacy glTF is unsupported";
    default:
        return "unknown cgltf error";
    }
}

bool isSafeRelativeUri(const char *pUri)
{
    if (pUri == nullptr || std::string_view(pUri).starts_with("data:"))
    {
        return true;
    }
    const std::string uri = pUri;
    if (uri.empty() || uri.find("://") != std::string::npos || uri[0] == '/' || uri[0] == '\\')
    {
        return false;
    }
    for (const std::filesystem::path &component : std::filesystem::path(uri))
    {
        if (component == "..")
        {
            return false;
        }
    }
    return true;
}

std::string joinedVirtualPath(const std::string &modelPath, const std::string &relativePath)
{
    const std::filesystem::path parent = std::filesystem::path(modelPath).parent_path();
    return (parent / relativePath).lexically_normal().generic_string();
}

bool hasPngSignature(const std::vector<uint8_t> &bytes)
{
    constexpr std::array<uint8_t, 8> Signature = {137, 80, 78, 71, 13, 10, 26, 10};
    return bytes.size() >= Signature.size() && std::equal(Signature.begin(), Signature.end(), bytes.begin());
}

const cgltf_accessor *findAttribute(const cgltf_primitive &primitive, cgltf_attribute_type type, int index = 0)
{
    for (size_t attributeIndex = 0; attributeIndex < primitive.attributes_count; ++attributeIndex)
    {
        const cgltf_attribute &attribute = primitive.attributes[attributeIndex];
        if (attribute.type == type && attribute.index == index)
        {
            return attribute.data;
        }
    }
    return nullptr;
}

bool readAccessor(const cgltf_accessor &accessor, size_t index, size_t count, float *pValues)
{
    std::array<float, 16> values = {};
    if (count > values.size() || cgltf_accessor_read_float(&accessor, index, values.data(), count) == 0)
    {
        return false;
    }
    if (!std::all_of(values.begin(), values.begin() + count, [](float value) { return std::isfinite(value); }))
    {
        return false;
    }
    std::copy_n(values.data(), count, pValues);
    return true;
}

void expandBounds(ModelBounds &bounds, const std::array<float, 3> &point)
{
    if (!bounds.valid)
    {
        bounds.min = point;
        bounds.max = point;
        bounds.valid = true;
        return;
    }
    for (size_t axis = 0; axis < 3; ++axis)
    {
        bounds.min[axis] = std::min(bounds.min[axis], point[axis]);
        bounds.max[axis] = std::max(bounds.max[axis], point[axis]);
    }
}

std::array<float, 3> transformPoint(const ModelMatrix &matrix, const std::array<float, 3> &point)
{
    return {
        matrix[0] * point[0] + matrix[4] * point[1] + matrix[8] * point[2] + matrix[12],
        matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
        matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14],
    };
}

bool visitHierarchy(
    const ModelAsset &asset,
    uint32_t nodeIndex,
    std::vector<uint8_t> &states,
    std::vector<uint32_t> &order,
    std::string &error
)
{
    if (states[nodeIndex] == 1)
    {
        error = "model node hierarchy contains a cycle at node " + std::to_string(nodeIndex);
        return false;
    }
    if (states[nodeIndex] == 2)
    {
        return true;
    }

    states[nodeIndex] = 1;
    order.push_back(nodeIndex);
    for (uint32_t childIndex : asset.nodes[nodeIndex].childIndices)
    {
        if (!visitHierarchy(asset, childIndex, states, order, error))
        {
            return false;
        }
    }
    states[nodeIndex] = 2;
    return true;
}

bool buildHierarchy(ModelAsset &asset, std::string &error)
{
    std::vector<uint8_t> states(asset.nodes.size(), 0);
    for (uint32_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        if (asset.nodes[nodeIndex].parentIndex < 0 &&
            !visitHierarchy(asset, nodeIndex, states, asset.hierarchyOrder, error))
        {
            return false;
        }
    }
    if (asset.hierarchyOrder.size() != asset.nodes.size())
    {
        error = "model node hierarchy has no root for one or more nodes";
        return false;
    }
    return true;
}

bool loadImages(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    const cgltf_data &data,
    ModelAsset &asset,
    std::string &error
)
{
    asset.images.reserve(data.images_count);
    for (size_t imageIndex = 0; imageIndex < data.images_count; ++imageIndex)
    {
        const cgltf_image &source = data.images[imageIndex];
        ModelImage image;
        image.name = source.name != nullptr ? source.name : "";
        if (source.buffer_view != nullptr)
        {
            if (source.mime_type == nullptr || std::string_view(source.mime_type) != "image/png")
            {
                error = "embedded model image " + std::to_string(imageIndex) + " is not PNG";
                return false;
            }
            const uint8_t *pBytes = cgltf_buffer_view_data(source.buffer_view);
            if (pBytes == nullptr)
            {
                error = "embedded model image " + std::to_string(imageIndex) + " has no buffer data";
                return false;
            }
            image.pngBytes.assign(pBytes, pBytes + source.buffer_view->size);
            image.sourcePath = virtualPath + "#image" + std::to_string(imageIndex);
        }
        else if (source.uri != nullptr)
        {
            if (!isSafeRelativeUri(source.uri) || std::string_view(source.uri).starts_with("data:"))
            {
                error = "model image URI must be a package-relative PNG path: " + std::string(source.uri);
                return false;
            }
            image.sourcePath = joinedVirtualPath(virtualPath, source.uri);
            const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(image.sourcePath);
            if (!bytes)
            {
                error = "model image was not found: " + image.sourcePath;
                return false;
            }
            image.pngBytes = *bytes;
        }
        else
        {
            error = "model image " + std::to_string(imageIndex) + " has neither URI nor buffer view";
            return false;
        }
        if (!hasPngSignature(image.pngBytes))
        {
            error = "model image is not a PNG: " + image.sourcePath;
            return false;
        }
        asset.images.push_back(std::move(image));
    }
    return true;
}

bool rejectUnsupportedFeatures(const cgltf_data &data, std::string &error)
{
    for (size_t animationIndex = 0; animationIndex < data.animations_count; ++animationIndex)
    {
        const cgltf_animation &animation = data.animations[animationIndex];
        for (size_t samplerIndex = 0; samplerIndex < animation.samplers_count; ++samplerIndex)
        {
            if (animation.samplers[samplerIndex].interpolation == cgltf_interpolation_type_cubic_spline)
            {
                const std::string name = animation.name != nullptr ? animation.name : std::to_string(animationIndex);
                error = "animation " + name + " uses unsupported CUBICSPLINE interpolation";
                return false;
            }
        }
    }
    return true;
}

bool loadMaterialTexture(const cgltf_data &data, const cgltf_texture_view &view,
    int &imageIndex, ModelSampler &sampler, std::string &error)
{
    if (view.texture == nullptr)
    {
        return true;
    }
    if (view.texcoord != 0 || view.has_transform || view.texture->image == nullptr)
    {
        error = "material texture requires UV0, an image, and no texture transform";
        return false;
    }
    imageIndex = int(cgltf_image_index(&data, view.texture->image));
    if (view.texture->sampler != nullptr)
    {
        const cgltf_sampler &source = *view.texture->sampler;
        sampler = {source.min_filter, source.mag_filter, source.wrap_s, source.wrap_t};
    }
    const auto validWrap = [](int value) { return value == 10497 || value == 33071 || value == 33648; };
    if (!validWrap(sampler.wrapS) || !validWrap(sampler.wrapT)
        || (sampler.magFilter != 0 && sampler.magFilter != 9728 && sampler.magFilter != 9729)
        || (sampler.minFilter != 0 && sampler.minFilter != 9728 && sampler.minFilter != 9729
            && (sampler.minFilter < 9984 || sampler.minFilter > 9987)))
    {
        error = "material texture has an invalid sampler";
        return false;
    }
    return true;
}

bool loadMaterials(const cgltf_data &data, ModelAsset &asset, std::string &error)
{
    asset.materials.reserve(data.materials_count);
    for (size_t materialIndex = 0; materialIndex < data.materials_count; ++materialIndex)
    {
        const cgltf_material &source = data.materials[materialIndex];
        if (source.has_pbr_specular_glossiness || source.has_clearcoat || source.has_transmission ||
            source.has_volume ||
            source.has_ior || source.has_specular || source.has_sheen || source.has_iridescence ||
            source.has_diffuse_transmission || source.has_anisotropy || source.has_dispersion)
        {
            error = "material " + std::to_string(materialIndex) + " uses an unsupported material extension";
            return false;
        }

        ModelMaterial material;
        material.name = source.name != nullptr ? source.name : "";
        material.doubleSided = source.double_sided != 0;
        material.unlit = source.unlit != 0;
        std::copy_n(source.emissive_factor, 3, material.emissive.begin());
        if (!loadMaterialTexture(data, source.normal_texture, material.normalImageIndex,
                material.normalSampler, error))
        {
            return false;
        }
        material.normalScale = source.normal_texture.scale;
        material.alphaCutoff = source.alpha_cutoff;
        switch (source.alpha_mode)
        {
        case cgltf_alpha_mode_opaque:
            material.alphaMode = ModelAlphaMode::Opaque;
            break;
        case cgltf_alpha_mode_mask:
            material.alphaMode = ModelAlphaMode::Mask;
            break;
        case cgltf_alpha_mode_blend:
            material.alphaMode = ModelAlphaMode::Blend;
            break;
        default:
            error = "material " + std::to_string(materialIndex) + " has an invalid alpha mode";
            return false;
        }

        if (source.has_pbr_metallic_roughness)
        {
            std::copy_n(source.pbr_metallic_roughness.base_color_factor, 4, material.baseColor.begin());
            material.metallic = source.pbr_metallic_roughness.metallic_factor;
            material.roughness = source.pbr_metallic_roughness.roughness_factor;
            if (!loadMaterialTexture(data, source.pbr_metallic_roughness.base_color_texture,
                    material.imageIndex, material.baseSampler, error)
                || !loadMaterialTexture(data, source.pbr_metallic_roughness.metallic_roughness_texture,
                    material.metallicRoughnessImageIndex, material.metallicRoughnessSampler, error))
            {
                return false;
            }
        }
        const auto unitValue = [](float value) { return std::isfinite(value) && value >= 0 && value <= 1; };
        if (!std::all_of(material.baseColor.begin(), material.baseColor.end(), unitValue)
            || !unitValue(material.metallic) || !unitValue(material.roughness)
            || !std::isfinite(material.alphaCutoff) || material.alphaCutoff < 0.0f
            || !std::isfinite(material.normalScale) || material.normalScale < 0
            || !std::all_of(material.emissive.begin(), material.emissive.end(), unitValue))
        {
            error = "material " + std::to_string(materialIndex) + " has invalid colour or surface factors";
            return false;
        }
        asset.materials.push_back(std::move(material));
    }
    return true;
}

bool loadMeshes(const cgltf_data &data, ModelAsset &asset, std::string &error)
{
    asset.meshes.reserve(data.meshes_count);
    for (size_t meshIndex = 0; meshIndex < data.meshes_count; ++meshIndex)
    {
        const cgltf_mesh &sourceMesh = data.meshes[meshIndex];
        ModelMesh mesh;
        mesh.name = sourceMesh.name != nullptr ? sourceMesh.name : "";
        cgltf_size extrasSize = 0;
        cgltf_copy_extras_json(&data, &sourceMesh.extras, nullptr, &extrasSize);
        if (extrasSize > 1)
        {
            try
            {
                std::string json(extrasSize, '\0');
                if (cgltf_copy_extras_json(&data, &sourceMesh.extras, json.data(), &extrasSize)
                    != cgltf_result_success)
                {
                    error = "cannot read model mesh LOD metadata";
                    return false;
                }
                const YAML::Node extras = YAML::Load(json.c_str());
                for (const char *pKey : {"openyamm_lods", "openyamm_shadow_lods"})
                {
                    if (!extras[pKey])
                    {
                        continue;
                    }
                    std::vector<uint32_t> &indices = std::string_view(pKey) == "openyamm_lods"
                        ? mesh.lodMeshes : mesh.shadowMeshes;
                    indices = extras[pKey].as<std::vector<uint32_t>>();
                    const size_t maximum = std::string_view(pKey) == "openyamm_lods" ? 3 : 4;
                    if (indices.empty() || indices.size() > maximum)
                    {
                        error = "model mesh LOD chain must contain at most four levels";
                        return false;
                    }
                    std::unordered_set<uint32_t> unique;
                    for (uint32_t index : indices)
                    {
                        if (index >= data.meshes_count || index == meshIndex || !unique.insert(index).second)
                        {
                            error = "model mesh LOD reference is invalid or duplicated";
                            return false;
                        }
                    }
                }
            }
            catch (const YAML::Exception &exception)
            {
                error = std::string("invalid model mesh LOD metadata: ") + exception.what();
                return false;
            }
        }
        const size_t targetCount = sourceMesh.primitives_count != 0 ? sourceMesh.primitives[0].targets_count : 0;
        mesh.weights.resize(targetCount, 0.0f);
        if (sourceMesh.weights_count != 0)
        {
            if (sourceMesh.weights_count != targetCount)
            {
                error = "mesh morph weight count differs from its target count";
                return false;
            }
            std::copy_n(sourceMesh.weights, targetCount, mesh.weights.begin());
        }
        mesh.primitives.reserve(sourceMesh.primitives_count);
        for (size_t primitiveIndex = 0; primitiveIndex < sourceMesh.primitives_count; ++primitiveIndex)
        {
            const cgltf_primitive &source = sourceMesh.primitives[primitiveIndex];
            if (source.type != cgltf_primitive_type_triangles)
            {
                error = "mesh " + std::to_string(meshIndex) + " primitive " + std::to_string(primitiveIndex) +
                    " is not a triangle list";
                return false;
            }
            if (source.targets_count != targetCount)
            {
                error = "mesh primitives have inconsistent morph target counts";
                return false;
            }

            const cgltf_accessor *pPosition = findAttribute(source, cgltf_attribute_type_position);
            const cgltf_accessor *pNormal = findAttribute(source, cgltf_attribute_type_normal);
            const cgltf_accessor *pTexCoord = findAttribute(source, cgltf_attribute_type_texcoord);
            if (pPosition == nullptr || pPosition->type != cgltf_type_vec3)
            {
                error = "mesh " + std::to_string(meshIndex) + " primitive " + std::to_string(primitiveIndex) +
                    " has no VEC3 POSITION attribute";
                return false;
            }
            if (pNormal != nullptr && (pNormal->type != cgltf_type_vec3 || pNormal->count != pPosition->count))
            {
                error = "mesh " + std::to_string(meshIndex) + " has an invalid NORMAL attribute";
                return false;
            }
            if (pTexCoord != nullptr && (pTexCoord->type != cgltf_type_vec2 || pTexCoord->count != pPosition->count))
            {
                error = "mesh " + std::to_string(meshIndex) + " has an invalid TEXCOORD_0 attribute";
                return false;
            }

            ModelPrimitive primitive;
            primitive.materialIndex = source.material != nullptr
                ? static_cast<int>(cgltf_material_index(&data, source.material)) : -1;
            primitive.vertices.resize(pPosition->count);
            for (size_t vertexIndex = 0; vertexIndex < pPosition->count; ++vertexIndex)
            {
                ModelVertex &vertex = primitive.vertices[vertexIndex];
                if (!readAccessor(*pPosition, vertexIndex, 3, vertex.position.data()) ||
                    (pNormal != nullptr && !readAccessor(*pNormal, vertexIndex, 3, vertex.normal.data())) ||
                    (pTexCoord != nullptr && !readAccessor(*pTexCoord, vertexIndex, 2, vertex.texCoord.data())))
                {
                    error = "mesh " + std::to_string(meshIndex) + " contains unreadable vertex data";
                    return false;
                }
            }

            for (size_t attributeIndex = 0; attributeIndex < source.attributes_count; ++attributeIndex)
            {
                const cgltf_attribute &attribute = source.attributes[attributeIndex];
                if ((attribute.type == cgltf_attribute_type_joints || attribute.type == cgltf_attribute_type_weights)
                    && (attribute.index < 0 || attribute.index > 1))
                {
                    error = "model supports at most eight joint influences per vertex";
                    return false;
                }
            }
            for (int set = 0; set < 2; ++set)
            {
                const cgltf_accessor *pJoints = findAttribute(source, cgltf_attribute_type_joints, set);
                const cgltf_accessor *pWeights = findAttribute(source, cgltf_attribute_type_weights, set);
                if (pJoints == nullptr && pWeights == nullptr)
                {
                    continue;
                }
                if (pJoints == nullptr || pWeights == nullptr || pJoints->type != cgltf_type_vec4
                    || pWeights->type != cgltf_type_vec4 || pJoints->count != pPosition->count
                    || pWeights->count != pPosition->count || (set == 1 && primitive.influences.empty()))
                {
                    error = "invalid paired JOINTS/WEIGHTS accessors";
                    return false;
                }
                primitive.influences.resize(pPosition->count);
                for (size_t vertexIndex = 0; vertexIndex < pPosition->count; ++vertexIndex)
                {
                    std::array<float, 4> joints = {}, weights = {};
                    if (!readAccessor(*pJoints, vertexIndex, 4, joints.data())
                        || !readAccessor(*pWeights, vertexIndex, 4, weights.data()))
                    {
                        error = "unreadable joint influence data";
                        return false;
                    }
                    for (size_t influence = 0; influence < 4; ++influence)
                    {
                        if (joints[influence] < 0 || joints[influence] > 65535
                            || std::floor(joints[influence]) != joints[influence] || weights[influence] < 0)
                        {
                            error = "invalid joint index or weight";
                            return false;
                        }
                        primitive.influences[vertexIndex].joints[set * 4 + influence] = uint16_t(joints[influence]);
                        primitive.influences[vertexIndex].weights[set * 4 + influence] = weights[influence];
                    }
                }
            }
            for (ModelVertexInfluences &influences : primitive.influences)
            {
                float sum = 0.0f;
                for (float weight : influences.weights)
                {
                    sum += weight;
                }
                if (std::abs(sum - 1.0f) > 0.001f)
                {
                    error = "joint weights must sum to one";
                    return false;
                }
                for (float &weight : influences.weights)
                {
                    weight /= sum;
                }
            }
            for (size_t targetIndex = 0; targetIndex < source.targets_count; ++targetIndex)
            {
                ModelMorphTarget target;
                const cgltf_morph_target &sourceTarget = source.targets[targetIndex];
                for (size_t attributeIndex = 0; attributeIndex < sourceTarget.attributes_count; ++attributeIndex)
                {
                    const cgltf_attribute &attribute = sourceTarget.attributes[attributeIndex];
                    if (attribute.type != cgltf_attribute_type_position
                        && attribute.type != cgltf_attribute_type_normal)
                    {
                        error = "unsupported morph target attribute";
                        return false;
                    }
                    if (attribute.data == nullptr || attribute.data->type != cgltf_type_vec3
                        || attribute.data->count != pPosition->count)
                    {
                        error = "invalid morph target accessor";
                        return false;
                    }
                    std::vector<std::array<float, 3>> &values = attribute.type == cgltf_attribute_type_position
                        ? target.positions : target.normals;
                    values.resize(pPosition->count);
                    for (size_t vertexIndex = 0; vertexIndex < pPosition->count; ++vertexIndex)
                    {
                        if (!readAccessor(*attribute.data, vertexIndex, 3, values[vertexIndex].data()))
                        {
                            error = "unreadable morph target data";
                            return false;
                        }
                    }
                }
                primitive.morphTargets.push_back(std::move(target));
            }
            const size_t indexCount = source.indices != nullptr ? source.indices->count : pPosition->count;
            if (indexCount % 3 != 0)
            {
                error = "mesh " + std::to_string(meshIndex) + " triangle index count is not divisible by three";
                return false;
            }
            primitive.indices.reserve(indexCount);
            for (size_t index = 0; index < indexCount; ++index)
            {
                const size_t vertexIndex = source.indices != nullptr
                    ? cgltf_accessor_read_index(source.indices, index) : index;
                if (vertexIndex >= primitive.vertices.size() || vertexIndex > std::numeric_limits<uint32_t>::max())
                {
                    error = "mesh " + std::to_string(meshIndex) + " contains an out-of-range index";
                    return false;
                }
                primitive.indices.push_back(static_cast<uint32_t>(vertexIndex));
            }
            mesh.primitives.push_back(std::move(primitive));
        }
        asset.meshes.push_back(std::move(mesh));
    }
    return true;
}

bool loadNodes(const cgltf_data &data, ModelAsset &asset, std::string &error)
{
    asset.nodes.resize(data.nodes_count);
    for (size_t nodeIndex = 0; nodeIndex < data.nodes_count; ++nodeIndex)
    {
        const cgltf_node &source = data.nodes[nodeIndex];
        if (source.has_mesh_gpu_instancing)
        {
            error = "node " + std::to_string(nodeIndex) + " uses unsupported GPU instancing";
            return false;
        }

        ModelNode &node = asset.nodes[nodeIndex];
        node.name = source.name != nullptr ? source.name : "";
        node.parentIndex = source.parent != nullptr ? static_cast<int>(cgltf_node_index(&data, source.parent)) : -1;
        node.meshIndex = source.mesh != nullptr ? static_cast<int>(cgltf_mesh_index(&data, source.mesh)) : -1;
        node.skinIndex = source.skin != nullptr ? int(cgltf_skin_index(&data, source.skin)) : -1;
        if (node.meshIndex >= 0)
        {
            node.weights = asset.meshes[node.meshIndex].weights;
        }
        if (source.weights_count != 0)
        {
            if (source.weights_count != node.weights.size())
            {
                error = "node morph weight count differs from its mesh";
                return false;
            }
            std::copy_n(source.weights, source.weights_count, node.weights.begin());
        }
        for (float weight : node.weights)
        {
            if (!std::isfinite(weight))
            {
                error = "non-finite default morph weight";
                return false;
            }
        }
        node.usesMatrix = source.has_matrix != 0;
        if (node.usesMatrix)
        {
            std::copy_n(source.matrix, 16, node.matrix.begin());
        }
        else
        {
            std::copy_n(source.translation, 3, node.transform.translation.begin());
            std::copy_n(source.rotation, 4, node.transform.rotation.begin());
            std::copy_n(source.scale, 3, node.transform.scale.begin());
            node.matrix = composeModelTransform(node.transform);
        }
        node.childIndices.reserve(source.children_count);
        for (size_t childIndex = 0; childIndex < source.children_count; ++childIndex)
        {
            node.childIndices.push_back(static_cast<uint32_t>(cgltf_node_index(&data, source.children[childIndex])));
        }
        if (!node.name.empty())
        {
            const auto [iterator, inserted] = asset.nodeIndicesByName.emplace(node.name, nodeIndex);
            if (!inserted)
            {
                error = "duplicate model node name: " + node.name + " (indices " +
                    std::to_string(iterator->second) + " and " + std::to_string(nodeIndex) + ")";
                return false;
            }
        }
    }
    return buildHierarchy(asset, error);
}

bool loadSkins(const cgltf_data &data, ModelAsset &asset, std::string &error)
{
    for (size_t skinIndex = 0; skinIndex < data.skins_count; ++skinIndex)
    {
        const cgltf_skin &source = data.skins[skinIndex];
        if (source.joints_count == 0 || source.joints_count > 65536
            || (source.inverse_bind_matrices != nullptr
                && (source.inverse_bind_matrices->type != cgltf_type_mat4
                    || source.inverse_bind_matrices->count != source.joints_count)))
        {
            error = "invalid skin joints or inverse bind matrices";
            return false;
        }
        ModelSkin skin;
        skin.inverseBindMatrices.resize(source.joints_count, identityModelMatrix());
        for (size_t joint = 0; joint < source.joints_count; ++joint)
        {
            skin.joints.push_back(uint32_t(cgltf_node_index(&data, source.joints[joint])));
            if (source.inverse_bind_matrices != nullptr
                && !readAccessor(*source.inverse_bind_matrices, joint, 16, skin.inverseBindMatrices[joint].data()))
            {
                error = "unreadable inverse bind matrix";
                return false;
            }
        }
        asset.skins.push_back(std::move(skin));
    }
    for (const ModelNode &node : asset.nodes)
    {
        if (node.skinIndex < 0 || node.meshIndex < 0)
        {
            continue;
        }
        std::vector<uint32_t> meshes = {uint32_t(node.meshIndex)};
        const ModelMesh &mesh = asset.meshes[node.meshIndex];
        meshes.insert(meshes.end(), mesh.lodMeshes.begin(), mesh.lodMeshes.end());
        meshes.insert(meshes.end(), mesh.shadowMeshes.begin(), mesh.shadowMeshes.end());
        for (uint32_t meshIndex : meshes)
        {
            for (const ModelPrimitive &primitive : asset.meshes[meshIndex].primitives)
            {
                if (primitive.influences.empty())
                {
                    error = "skinned primitive has no joint influences";
                    return false;
                }
                for (const ModelVertexInfluences &influences : primitive.influences)
                {
                    for (size_t i = 0; i < influences.joints.size(); ++i)
                    {
                        if (influences.weights[i] > 0
                            && influences.joints[i] >= asset.skins[node.skinIndex].joints.size())
                        {
                            error = "vertex joint index exceeds its skin";
                            return false;
                        }
                    }
                }
            }
        }
    }
    return true;
}

bool validateMeshLods(const ModelAsset &asset, std::string &error)
{
    for (const ModelMesh &mesh : asset.meshes)
    {
        if ((!mesh.lodMeshes.empty() || !mesh.shadowMeshes.empty()) && !mesh.weights.empty())
        {
            error = "mesh LODs require skeletal or static geometry, not morph targets";
            return false;
        }
        for (const std::vector<uint32_t> *pChain : {&mesh.lodMeshes, &mesh.shadowMeshes})
        {
            for (uint32_t index : *pChain)
            {
                const ModelMesh &lower = asset.meshes[index];
                if (lower.primitives.empty() || !lower.weights.empty()
                    || !lower.lodMeshes.empty() || !lower.shadowMeshes.empty())
                {
                    error = "LOD meshes must not contain morph targets or nested LOD chains";
                    return false;
                }
                for (const ModelNode &node : asset.nodes)
                {
                    if (node.meshIndex == int(index))
                    {
                        error = "LOD meshes must be referenced only by their owning mesh";
                        return false;
                    }
                }
                if (pChain == &mesh.shadowMeshes)
                {
                    for (const ModelPrimitive &primitive : lower.primitives)
                    {
                        if (primitive.materialIndex >= 0
                            && asset.materials[primitive.materialIndex].alphaMode != ModelAlphaMode::Opaque)
                        {
                            error = "dedicated shadow LODs require opaque geometry";
                            return false;
                        }
                    }
                }
            }
        }
    }
    return true;
}

bool loadAnimations(const cgltf_data &data, ModelAsset &asset, std::string &error)
{
    asset.clips.reserve(data.animations_count);
    for (size_t animationIndex = 0; animationIndex < data.animations_count; ++animationIndex)
    {
        const cgltf_animation &sourceAnimation = data.animations[animationIndex];
        ModelAnimationClip clip;
        clip.name = sourceAnimation.name != nullptr && sourceAnimation.name[0] != '\0'
            ? sourceAnimation.name : "clip_" + std::to_string(animationIndex);
        if (!asset.clipIndicesByName.emplace(clip.name, animationIndex).second)
        {
            error = "duplicate model animation name: " + clip.name;
            return false;
        }
        std::unordered_set<uint64_t> animatedTargets;
        clip.channels.reserve(sourceAnimation.channels_count);
        for (size_t channelIndex = 0; channelIndex < sourceAnimation.channels_count; ++channelIndex)
        {
            const cgltf_animation_channel &sourceChannel = sourceAnimation.channels[channelIndex];
            if (sourceChannel.target_node == nullptr || sourceChannel.sampler == nullptr)
            {
                error = "animation " + clip.name + " contains an unbound channel";
                return false;
            }
            if (sourceChannel.sampler->interpolation == cgltf_interpolation_type_cubic_spline)
            {
                error = "animation " + clip.name + " uses unsupported CUBICSPLINE interpolation";
                return false;
            }
            if (sourceChannel.sampler->interpolation != cgltf_interpolation_type_linear &&
                sourceChannel.sampler->interpolation != cgltf_interpolation_type_step)
            {
                error = "animation " + clip.name + " uses an invalid interpolation mode";
                return false;
            }

            ModelAnimationChannel channel;
            channel.nodeIndex = static_cast<uint32_t>(cgltf_node_index(&data, sourceChannel.target_node));
            channel.interpolation = sourceChannel.sampler->interpolation == cgltf_interpolation_type_step
                ? ModelAnimationInterpolation::Step : ModelAnimationInterpolation::Linear;
            size_t valueComponentCount = 0;
            switch (sourceChannel.target_path)
            {
            case cgltf_animation_path_type_translation:
                channel.target = ModelAnimationTarget::Translation;
                valueComponentCount = 3;
                break;
            case cgltf_animation_path_type_rotation:
                channel.target = ModelAnimationTarget::Rotation;
                valueComponentCount = 4;
                break;
            case cgltf_animation_path_type_scale:
                channel.target = ModelAnimationTarget::Scale;
                valueComponentCount = 3;
                break;
            case cgltf_animation_path_type_weights:
                channel.target = ModelAnimationTarget::Weights;
                valueComponentCount = asset.nodes[channel.nodeIndex].weights.size();
                if (valueComponentCount == 0)
                {
                    error = "weight animation targets a node without morph targets";
                    return false;
                }
                break;
            default:
                error = "animation " + clip.name + " uses an invalid target path";
                return false;
            }
            if (channel.target != ModelAnimationTarget::Weights && asset.nodes[channel.nodeIndex].usesMatrix)
            {
                error = "animation " + clip.name + " targets matrix node " +
                    std::to_string(channel.nodeIndex) + " with TRS data";
                return false;
            }
            const uint64_t targetKey = static_cast<uint64_t>(channel.nodeIndex) * 5 +
                static_cast<uint64_t>(channel.target);
            if (!animatedTargets.insert(targetKey).second)
            {
                error = "animation " + clip.name + " contains duplicate channels for one node property";
                return false;
            }

            const cgltf_accessor *pTimes = sourceChannel.sampler->input;
            const cgltf_accessor *pValues = sourceChannel.sampler->output;
            if (pTimes == nullptr || pValues == nullptr || pTimes->type != cgltf_type_scalar ||
                pTimes->component_type != cgltf_component_type_r_32f || pTimes->count == 0 ||
                pValues->count != pTimes->count * (channel.target == ModelAnimationTarget::Weights
                    ? valueComponentCount : 1))
            {
                error = "animation " + clip.name + " has invalid sampler accessors";
                return false;
            }
            if (channel.target == ModelAnimationTarget::Weights ? pValues->type != cgltf_type_scalar :
                ((valueComponentCount == 3 && pValues->type != cgltf_type_vec3) ||
                (valueComponentCount == 4 && pValues->type != cgltf_type_vec4)))
            {
                error = "animation " + clip.name + " has an invalid output accessor type";
                return false;
            }

            channel.times.resize(pTimes->count);
            channel.values.resize(pTimes->count);
            if (channel.target == ModelAnimationTarget::Weights)
            {
                channel.weightValues.resize(pTimes->count, std::vector<float>(valueComponentCount));
            }
            for (size_t keyIndex = 0; keyIndex < pTimes->count; ++keyIndex)
            {
                if (!readAccessor(*pTimes, keyIndex, 1, &channel.times[keyIndex]) ||
                    (channel.target != ModelAnimationTarget::Weights
                        && !readAccessor(*pValues, keyIndex, valueComponentCount, channel.values[keyIndex].data())))
                {
                    error = "animation " + clip.name + " contains unreadable keyframe data";
                    return false;
                }
                if (!std::isfinite(channel.times[keyIndex]) || channel.times[keyIndex] < 0.0f ||
                    (keyIndex != 0 && channel.times[keyIndex] <= channel.times[keyIndex - 1]))
                {
                    error = "animation " + clip.name + " keyframe times are not finite and strictly increasing";
                    return false;
                }
                for (size_t component = 0; component < valueComponentCount; ++component)
                {
                    if (channel.target == ModelAnimationTarget::Weights
                        ? !readAccessor(*pValues, keyIndex * valueComponentCount + component, 1,
                            &channel.weightValues[keyIndex][component])
                        : !std::isfinite(channel.values[keyIndex][component]))
                    {
                        error = "animation " + clip.name + " contains a non-finite keyframe value";
                        return false;
                    }
                }
            }
            clip.durationSeconds = std::max(clip.durationSeconds, channel.times.back());
            clip.channels.push_back(std::move(channel));
        }
        asset.clips.push_back(std::move(clip));
    }
    return true;
}

void calculateStaticBounds(ModelAsset &asset)
{
    ModelPose pose;
    resetModelPose(asset, pose);
    evaluateModelHierarchy(asset, identityModelMatrix(), pose);
    deformModelPose(asset, pose);
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        if (node.meshIndex < 0 || !modelMatrixVisible(pose.globalMatrices[nodeIndex]))
        {
            continue;
        }
        const ModelMesh &mesh = asset.meshes[node.meshIndex];
        for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
        {
            const ModelPrimitive &primitive = mesh.primitives[primitiveIndex];
            const std::vector<ModelVertex> &vertices = node.skinIndex >= 0 || !primitive.morphTargets.empty()
                ? pose.deformedVertices[nodeIndex][primitiveIndex] : primitive.vertices;
            const ModelMatrix matrix = node.skinIndex >= 0 ? identityModelMatrix() : pose.globalMatrices[nodeIndex];
            for (const ModelVertex &vertex : vertices)
            {
                expandBounds(asset.staticBounds, transformPoint(matrix, vertex.position));
            }
        }
    }
}
}

ModelLoadResult GltfModelLoader::load(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath
) const
{
    ModelLoadResult result;
    const std::optional<std::vector<uint8_t>> sourceBytes = assetFileSystem.readBinaryFile(virtualPath);
    if (!sourceBytes)
    {
        result.error = "model asset was not found: " + virtualPath;
        return result;
    }

    AssetFileContext fileContext = {&assetFileSystem};
    cgltf_options options = {};
    options.file.read = readAssetFile;
    options.file.release = releaseAssetFile;
    options.file.user_data = &fileContext;
    cgltf_data *pParsedData = nullptr;
    cgltf_result parseResult = cgltf_parse(&options, sourceBytes->data(), sourceBytes->size(), &pParsedData);
    if (parseResult != cgltf_result_success || pParsedData == nullptr)
    {
        result.error = "could not parse model " + virtualPath + ": " + cgltfResultName(parseResult);
        return result;
    }
    std::unique_ptr<cgltf_data, CgltfDeleter> data(pParsedData);

    if (data->extensions_required_count != 0)
    {
        result.error = "model " + virtualPath + " requires unsupported glTF extension " +
            std::string(data->extensions_required[0]);
        return result;
    }
    for (size_t bufferIndex = 0; bufferIndex < data->buffers_count; ++bufferIndex)
    {
        if (!isSafeRelativeUri(data->buffers[bufferIndex].uri))
        {
            result.error = "model buffer URI must be package-relative: " +
                std::string(data->buffers[bufferIndex].uri);
            return result;
        }
    }
    for (size_t imageIndex = 0; imageIndex < data->images_count; ++imageIndex)
    {
        if (!isSafeRelativeUri(data->images[imageIndex].uri))
        {
            result.error = "model image URI must be package-relative: " + std::string(data->images[imageIndex].uri);
            return result;
        }
    }

    const cgltf_result bufferResult = cgltf_load_buffers(&options, data.get(), virtualPath.c_str());
    if (bufferResult != cgltf_result_success)
    {
        result.error = "could not load buffers for model " + virtualPath + ": " + cgltfResultName(bufferResult);
        return result;
    }
    if (!rejectUnsupportedFeatures(*data, result.error))
    {
        return result;
    }
    const cgltf_result validationResult = cgltf_validate(data.get());
    if (validationResult != cgltf_result_success)
    {
        result.error = "model " + virtualPath + " failed glTF validation: " + cgltfResultName(validationResult);
        return result;
    }

    std::shared_ptr<ModelAsset> asset = std::make_shared<ModelAsset>();
    asset->sourcePath = virtualPath;
    if (!loadImages(assetFileSystem, virtualPath, *data, *asset, result.error) ||
        !loadMaterials(*data, *asset, result.error) ||
        !loadMeshes(*data, *asset, result.error) ||
        !loadNodes(*data, *asset, result.error) ||
        !validateMeshLods(*asset, result.error) ||
        !loadSkins(*data, *asset, result.error) ||
        !loadAnimations(*data, *asset, result.error))
    {
        return result;
    }
    calculateStaticBounds(*asset);
    result.asset = std::move(asset);
    return result;
}

ModelLoadResult ModelAssetCache::load(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath
)
{
    const auto iterator = m_assets.find(virtualPath);
    if (iterator != m_assets.end())
    {
        return {iterator->second, {}, {}};
    }
    ModelLoadResult result = m_loader.load(assetFileSystem, virtualPath);
    if (result)
    {
        m_assets.emplace(virtualPath, result.asset);
    }
    return result;
}

void ModelAssetCache::clear()
{
    m_assets.clear();
}

size_t ModelAssetCache::size() const
{
    return m_assets.size();
}
}
