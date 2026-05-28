#define CGLTF_IMPLEMENTATION
#include <cgltf/cgltf.h>

#include "game/render/AnimatedModelAsset.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <string_view>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::string stringValue(const char *pValue)
{
    return pValue != nullptr ? std::string(pValue) : std::string();
}

std::string lowerCopy(std::string_view value)
{
    std::string result(value);
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return result;
}

void addDiagnostic(AnimatedModelAsset &asset, bool error, const std::string &message)
{
    asset.diagnostics.push_back(AnimatedModelDiagnostic{message, error});
}

size_t nodeIndex(const cgltf_data &data, const cgltf_node *pNode)
{
    return static_cast<size_t>(pNode - data.nodes);
}

size_t materialIndex(const cgltf_data &data, const cgltf_material *pMaterial)
{
    if (pMaterial == nullptr)
    {
        return std::numeric_limits<size_t>::max();
    }

    return static_cast<size_t>(pMaterial - data.materials);
}

const cgltf_accessor *findAttributeAccessor(
    const cgltf_primitive &primitive,
    cgltf_attribute_type type)
{
    for (cgltf_size attributeIndex = 0; attributeIndex < primitive.attributes_count; ++attributeIndex)
    {
        const cgltf_attribute &attribute = primitive.attributes[attributeIndex];
        if (attribute.type == type)
        {
            return attribute.data;
        }
    }

    return nullptr;
}

AnimatedModelMat4 identityMatrix()
{
    return AnimatedModelMat4{};
}

AnimatedModelMat4 matrixFromAccessor(const cgltf_accessor &accessor, cgltf_size index)
{
    AnimatedModelMat4 result = {};
    float values[16] = {};
    if (cgltf_accessor_read_float(&accessor, index, values, 16) != 0)
    {
        std::copy(values, values + 16, result.values.begin());
    }
    return result;
}

AnimatedModelVec3 vec3FromAccessor(const cgltf_accessor *pAccessor, cgltf_size index)
{
    AnimatedModelVec3 result = {};
    if (pAccessor == nullptr)
    {
        return result;
    }

    float values[3] = {};
    cgltf_accessor_read_float(pAccessor, index, values, 3);
    result = {values[0], values[1], values[2]};
    return result;
}

std::array<float, 2> vec2FromAccessor(const cgltf_accessor *pAccessor, cgltf_size index)
{
    std::array<float, 2> result = {0.0f, 0.0f};
    if (pAccessor == nullptr)
    {
        return result;
    }

    float values[2] = {};
    cgltf_accessor_read_float(pAccessor, index, values, 2);
    result = {values[0], values[1]};
    return result;
}

std::array<uint32_t, 4> jointsFromAccessor(const cgltf_accessor *pAccessor, cgltf_size index)
{
    std::array<uint32_t, 4> result = {0, 0, 0, 0};
    if (pAccessor == nullptr)
    {
        return result;
    }

    cgltf_uint values[4] = {};
    cgltf_accessor_read_uint(pAccessor, index, values, 4);
    result = {values[0], values[1], values[2], values[3]};
    return result;
}

std::array<float, 4> weightsFromAccessor(const cgltf_accessor *pAccessor, cgltf_size index)
{
    std::array<float, 4> result = {0.0f, 0.0f, 0.0f, 0.0f};
    if (pAccessor == nullptr)
    {
        return result;
    }

    float values[4] = {};
    cgltf_accessor_read_float(pAccessor, index, values, 4);
    result = {values[0], values[1], values[2], values[3]};
    return result;
}

uint32_t indexFromAccessor(const cgltf_accessor *pAccessor, cgltf_size index)
{
    if (pAccessor == nullptr)
    {
        return 0;
    }

    cgltf_uint value = 0;
    cgltf_accessor_read_uint(pAccessor, index, &value, 1);
    return value;
}

void expandBounds(AnimatedModelBounds &bounds, const AnimatedModelVec3 &position)
{
    if (!bounds.valid)
    {
        bounds.min = position;
        bounds.max = position;
        bounds.valid = true;
        return;
    }

    bounds.min.x = std::min(bounds.min.x, position.x);
    bounds.min.y = std::min(bounds.min.y, position.y);
    bounds.min.z = std::min(bounds.min.z, position.z);
    bounds.max.x = std::max(bounds.max.x, position.x);
    bounds.max.y = std::max(bounds.max.y, position.y);
    bounds.max.z = std::max(bounds.max.z, position.z);
}

bool boundsAreFinite(const AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return false;
    }

    return std::isfinite(bounds.min.x) && std::isfinite(bounds.min.y) && std::isfinite(bounds.min.z)
        && std::isfinite(bounds.max.x) && std::isfinite(bounds.max.y) && std::isfinite(bounds.max.z);
}

bool vec3IsFinite(const AnimatedModelVec3 &value)
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

bool quatIsFinite(const AnimatedModelQuat &value)
{
    return std::isfinite(value.x) && std::isfinite(value.y)
        && std::isfinite(value.z) && std::isfinite(value.w);
}

bool transformIsFinite(const AnimatedModelTransform &transform)
{
    return vec3IsFinite(transform.translation)
        && quatIsFinite(transform.rotation)
        && vec3IsFinite(transform.scale);
}

AnimatedModelQuat normalizeQuat(AnimatedModelQuat quat)
{
    const float length = std::sqrt(quat.x * quat.x + quat.y * quat.y + quat.z * quat.z + quat.w * quat.w);
    if (length <= 0.0f)
    {
        return {};
    }

    quat.x /= length;
    quat.y /= length;
    quat.z /= length;
    quat.w /= length;
    return quat;
}

AnimatedModelVec3 lerpVec3(const AnimatedModelVec3 &a, const AnimatedModelVec3 &b, float amount)
{
    return {
        a.x + (b.x - a.x) * amount,
        a.y + (b.y - a.y) * amount,
        a.z + (b.z - a.z) * amount};
}

AnimatedModelQuat slerpQuat(AnimatedModelQuat a, AnimatedModelQuat b, float amount)
{
    a = normalizeQuat(a);
    b = normalizeQuat(b);

    float dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
    if (dot < 0.0f)
    {
        dot = -dot;
        b.x = -b.x;
        b.y = -b.y;
        b.z = -b.z;
        b.w = -b.w;
    }

    if (dot > 0.9995f)
    {
        return normalizeQuat({
            a.x + (b.x - a.x) * amount,
            a.y + (b.y - a.y) * amount,
            a.z + (b.z - a.z) * amount,
            a.w + (b.w - a.w) * amount});
    }

    const float theta0 = std::acos(std::clamp(dot, -1.0f, 1.0f));
    const float theta = theta0 * amount;
    const float sinTheta = std::sin(theta);
    const float sinTheta0 = std::sin(theta0);

    if (sinTheta0 == 0.0f)
    {
        return a;
    }

    const float scaleA = std::cos(theta) - dot * sinTheta / sinTheta0;
    const float scaleB = sinTheta / sinTheta0;
    return normalizeQuat({
        scaleA * a.x + scaleB * b.x,
        scaleA * a.y + scaleB * b.y,
        scaleA * a.z + scaleB * b.z,
        scaleA * a.w + scaleB * b.w});
}

AnimatedModelTransform blendTransform(
    const AnimatedModelTransform &from,
    const AnimatedModelTransform &to,
    float amount)
{
    return {
        lerpVec3(from.translation, to.translation, amount),
        slerpQuat(from.rotation, to.rotation, amount),
        lerpVec3(from.scale, to.scale, amount)};
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

AnimatedModelMat4 matrixFromTransform(const AnimatedModelTransform &transform)
{
    const AnimatedModelQuat quat = normalizeQuat(transform.rotation);
    const float xx = quat.x * quat.x;
    const float yy = quat.y * quat.y;
    const float zz = quat.z * quat.z;
    const float xy = quat.x * quat.y;
    const float xz = quat.x * quat.z;
    const float yz = quat.y * quat.z;
    const float wx = quat.w * quat.x;
    const float wy = quat.w * quat.y;
    const float wz = quat.w * quat.z;

    AnimatedModelMat4 result = {};
    result.values[0] = (1.0f - 2.0f * (yy + zz)) * transform.scale.x;
    result.values[1] = (2.0f * (xy + wz)) * transform.scale.x;
    result.values[2] = (2.0f * (xz - wy)) * transform.scale.x;
    result.values[4] = (2.0f * (xy - wz)) * transform.scale.y;
    result.values[5] = (1.0f - 2.0f * (xx + zz)) * transform.scale.y;
    result.values[6] = (2.0f * (yz + wx)) * transform.scale.y;
    result.values[8] = (2.0f * (xz + wy)) * transform.scale.z;
    result.values[9] = (2.0f * (yz - wx)) * transform.scale.z;
    result.values[10] = (1.0f - 2.0f * (xx + yy)) * transform.scale.z;
    result.values[12] = transform.translation.x;
    result.values[13] = transform.translation.y;
    result.values[14] = transform.translation.z;
    return result;
}

AnimatedModelTransform transformFromNode(const cgltf_node &node)
{
    AnimatedModelTransform result = {};

    if (node.has_translation)
    {
        result.translation = {node.translation[0], node.translation[1], node.translation[2]};
    }

    if (node.has_rotation)
    {
        result.rotation = normalizeQuat({node.rotation[0], node.rotation[1], node.rotation[2], node.rotation[3]});
    }

    if (node.has_scale)
    {
        result.scale = {node.scale[0], node.scale[1], node.scale[2]};
    }

    return result;
}

std::vector<float> readScalarAccessor(const cgltf_accessor *pAccessor)
{
    std::vector<float> result;
    if (pAccessor == nullptr)
    {
        return result;
    }

    result.resize(pAccessor->count);
    for (cgltf_size index = 0; index < pAccessor->count; ++index)
    {
        float value = 0.0f;
        cgltf_accessor_read_float(pAccessor, index, &value, 1);
        result[index] = value;
    }
    return result;
}

AnimatedModelTransform transformValueAt(
    const cgltf_accessor *pAccessor,
    cgltf_animation_path_type path,
    cgltf_size index)
{
    AnimatedModelTransform result = {};
    float values[4] = {};
    cgltf_accessor_read_float(pAccessor, index, values, 4);

    if (path == cgltf_animation_path_type_translation)
    {
        result.translation = {values[0], values[1], values[2]};
    }
    else if (path == cgltf_animation_path_type_rotation)
    {
        result.rotation = normalizeQuat({values[0], values[1], values[2], values[3]});
    }
    else if (path == cgltf_animation_path_type_scale)
    {
        result.scale = {values[0], values[1], values[2]};
    }

    return result;
}

AnimatedModelChannelPath channelPath(cgltf_animation_path_type path)
{
    if (path == cgltf_animation_path_type_translation)
    {
        return AnimatedModelChannelPath::Translation;
    }
    if (path == cgltf_animation_path_type_rotation)
    {
        return AnimatedModelChannelPath::Rotation;
    }
    if (path == cgltf_animation_path_type_scale)
    {
        return AnimatedModelChannelPath::Scale;
    }
    return AnimatedModelChannelPath::Unsupported;
}

float normalizeSampleTime(float timeSeconds, float durationSeconds, bool loop)
{
    if (durationSeconds <= 0.0f)
    {
        return 0.0f;
    }

    if (loop)
    {
        float result = std::fmod(timeSeconds, durationSeconds);
        if (result < 0.0f)
        {
            result += durationSeconds;
        }
        return result;
    }

    return std::clamp(timeSeconds, 0.0f, durationSeconds);
}

void applyChannelSample(
    AnimatedModelTransform &transform,
    const AnimatedModelChannel &channel,
    float timeSeconds)
{
    if (channel.timesSeconds.empty() || channel.transforms.empty())
    {
        return;
    }

    if (timeSeconds <= channel.timesSeconds.front() || channel.timesSeconds.size() == 1)
    {
        const AnimatedModelTransform &sample = channel.transforms.front();
        if (channel.path == AnimatedModelChannelPath::Translation)
        {
            transform.translation = sample.translation;
        }
        else if (channel.path == AnimatedModelChannelPath::Rotation)
        {
            transform.rotation = sample.rotation;
        }
        else if (channel.path == AnimatedModelChannelPath::Scale)
        {
            transform.scale = sample.scale;
        }
        return;
    }

    size_t upperIndex = 1;
    while (upperIndex < channel.timesSeconds.size() && channel.timesSeconds[upperIndex] < timeSeconds)
    {
        ++upperIndex;
    }

    if (upperIndex >= channel.timesSeconds.size())
    {
        const AnimatedModelTransform &sample = channel.transforms.back();
        if (channel.path == AnimatedModelChannelPath::Translation)
        {
            transform.translation = sample.translation;
        }
        else if (channel.path == AnimatedModelChannelPath::Rotation)
        {
            transform.rotation = sample.rotation;
        }
        else if (channel.path == AnimatedModelChannelPath::Scale)
        {
            transform.scale = sample.scale;
        }
        return;
    }

    const size_t lowerIndex = upperIndex - 1;
    const float lowerTime = channel.timesSeconds[lowerIndex];
    const float upperTime = channel.timesSeconds[upperIndex];
    const float span = upperTime - lowerTime;
    const float amount = span > 0.0f ? (timeSeconds - lowerTime) / span : 0.0f;
    const AnimatedModelTransform &lower = channel.transforms[lowerIndex];
    const AnimatedModelTransform &upper = channel.transforms[upperIndex];

    if (channel.path == AnimatedModelChannelPath::Translation)
    {
        transform.translation = lerpVec3(lower.translation, upper.translation, amount);
    }
    else if (channel.path == AnimatedModelChannelPath::Rotation)
    {
        transform.rotation = slerpQuat(lower.rotation, upper.rotation, amount);
    }
    else if (channel.path == AnimatedModelChannelPath::Scale)
    {
        transform.scale = lerpVec3(lower.scale, upper.scale, amount);
    }
}

std::vector<AnimatedModelTransform> sampleLocalTransforms(
    const AnimatedModelAsset &asset,
    const AnimatedModelClip *pClip,
    float timeSeconds,
    bool loop)
{
    std::vector<AnimatedModelTransform> localTransforms;
    localTransforms.reserve(asset.nodes.size());
    for (const AnimatedModelNode &node : asset.nodes)
    {
        localTransforms.push_back(node.bindTransform);
    }

    if (pClip != nullptr)
    {
        const float sampleTime = normalizeSampleTime(timeSeconds, pClip->durationSeconds, loop);
        for (const AnimatedModelChannel &channel : pClip->channels)
        {
            if (channel.nodeIndex < localTransforms.size())
            {
                applyChannelSample(localTransforms[channel.nodeIndex], channel, sampleTime);
            }
        }
    }

    return localTransforms;
}

AnimatedModelPose poseFromLocalTransforms(
    const AnimatedModelAsset &asset,
    std::vector<AnimatedModelTransform> localTransforms)
{
    AnimatedModelPose pose = {};
    pose.localTransforms = std::move(localTransforms);
    pose.globalTransforms.resize(asset.nodes.size());

    for (size_t nodeIndexValue = 0; nodeIndexValue < asset.nodes.size(); ++nodeIndexValue)
    {
        const AnimatedModelMat4 localMatrix = matrixFromTransform(pose.localTransforms[nodeIndexValue]);
        const int parentIndex = asset.nodes[nodeIndexValue].parentIndex;
        pose.globalTransforms[nodeIndexValue] =
            parentIndex >= 0
                ? multiplyMatrix(pose.globalTransforms[static_cast<size_t>(parentIndex)], localMatrix)
                : localMatrix;
    }

    if (!asset.skins.empty())
    {
        const AnimatedModelSkin &skin = asset.skins.front();
        pose.skinningMatrices.reserve(skin.joints.size());
        for (const AnimatedModelJoint &joint : skin.joints)
        {
            if (joint.nodeIndex < pose.globalTransforms.size())
            {
                pose.skinningMatrices.push_back(
                    multiplyMatrix(pose.globalTransforms[joint.nodeIndex], joint.inverseBindMatrix));
            }
        }
    }

    return pose;
}

void appendEventsInNormalizedInterval(
    const AnimatedModelClip &clip,
    float startSeconds,
    float endSeconds,
    bool includeStart,
    std::vector<AnimatedModelEvent> &events)
{
    if (endSeconds < startSeconds)
    {
        return;
    }

    for (const AnimatedModelEvent &event : clip.events)
    {
        const bool afterStart = includeStart
            ? event.timeSeconds >= startSeconds
            : event.timeSeconds > startSeconds;
        if (afterStart && event.timeSeconds <= endSeconds)
        {
            events.push_back(event);
        }
    }
}
}

const AnimatedModelClip *AnimatedModelAsset::findClip(std::string_view name) const
{
    const std::string loweredName = lowerCopy(name);
    for (const AnimatedModelClip &clip : clips)
    {
        if (lowerCopy(clip.name) == loweredName)
        {
            return &clip;
        }
    }
    return nullptr;
}

std::optional<size_t> AnimatedModelAsset::findNodeIndex(std::string_view name) const
{
    const std::string loweredName = lowerCopy(name);
    for (size_t index = 0; index < nodes.size(); ++index)
    {
        if (lowerCopy(nodes[index].name) == loweredName)
        {
            return index;
        }
    }
    return std::nullopt;
}

std::optional<size_t> AnimatedModelAsset::findSocketIndex(std::string_view name) const
{
    const std::string loweredName = lowerCopy(name);
    for (size_t index = 0; index < sockets.size(); ++index)
    {
        if (lowerCopy(sockets[index].name) == loweredName)
        {
            return index;
        }
    }
    return std::nullopt;
}

bool AnimatedModelAsset::hasErrors() const
{
    for (const AnimatedModelDiagnostic &diagnostic : diagnostics)
    {
        if (diagnostic.error)
        {
            return true;
        }
    }
    return false;
}

std::optional<AnimatedModelAsset> loadAnimatedModelAsset(
    const std::filesystem::path &path,
    std::string &errorMessage)
{
    cgltf_options options = {};
    cgltf_data *pData = nullptr;
    cgltf_result parseResult = cgltf_parse_file(&options, path.string().c_str(), &pData);
    if (parseResult != cgltf_result_success || pData == nullptr)
    {
        errorMessage = "failed to parse glTF/GLB: " + path.string();
        return std::nullopt;
    }

    const cgltf_result bufferResult = cgltf_load_buffers(&options, pData, path.string().c_str());
    if (bufferResult != cgltf_result_success)
    {
        cgltf_free(pData);
        errorMessage = "failed to load GLB buffers: " + path.string();
        return std::nullopt;
    }

    AnimatedModelAsset asset = {};
    asset.sourceId = path.stem().string();
    asset.sourcePath = path;
    asset.nodes.reserve(pData->nodes_count);
    for (cgltf_size nodeIndexValue = 0; nodeIndexValue < pData->nodes_count; ++nodeIndexValue)
    {
        const cgltf_node &node = pData->nodes[nodeIndexValue];
        AnimatedModelNode modelNode = {};
        modelNode.name = stringValue(node.name);
        modelNode.parentIndex = node.parent != nullptr ? static_cast<int>(nodeIndex(*pData, node.parent)) : -1;
        modelNode.bindTransform = transformFromNode(node);
        modelNode.hasMesh = node.mesh != nullptr;
        if (node.skin != nullptr)
        {
            modelNode.skinIndex = static_cast<size_t>(node.skin - pData->skins);
        }

        for (cgltf_size childIndex = 0; childIndex < node.children_count; ++childIndex)
        {
            modelNode.childIndices.push_back(nodeIndex(*pData, node.children[childIndex]));
        }

        asset.nodes.push_back(std::move(modelNode));
    }

    asset.materials.reserve(pData->materials_count);
    for (cgltf_size materialIndexValue = 0; materialIndexValue < pData->materials_count; ++materialIndexValue)
    {
        const cgltf_material &material = pData->materials[materialIndexValue];
        AnimatedModelMaterial modelMaterial = {};
        modelMaterial.name = stringValue(material.name);
        modelMaterial.alphaMask = material.alpha_mode == cgltf_alpha_mode_mask;
        modelMaterial.alphaBlend = material.alpha_mode == cgltf_alpha_mode_blend;
        modelMaterial.alphaCutoff = material.alpha_cutoff;
        modelMaterial.doubleSided = material.double_sided != 0;
        if (material.has_pbr_metallic_roughness)
        {
            const cgltf_texture *pTexture = material.pbr_metallic_roughness.base_color_texture.texture;
            if (pTexture != nullptr && pTexture->image != nullptr)
            {
                modelMaterial.baseColorTextureUri = stringValue(pTexture->image->uri);
            }
        }
        asset.materials.push_back(std::move(modelMaterial));
    }

    for (cgltf_size meshIndex = 0; meshIndex < pData->meshes_count; ++meshIndex)
    {
        const cgltf_mesh &mesh = pData->meshes[meshIndex];
        for (cgltf_size primitiveIndex = 0; primitiveIndex < mesh.primitives_count; ++primitiveIndex)
        {
            const cgltf_primitive &primitive = mesh.primitives[primitiveIndex];
            AnimatedModelPrimitive modelPrimitive = {};
            modelPrimitive.meshIndex = meshIndex;
            modelPrimitive.primitiveIndex = primitiveIndex;
            modelPrimitive.materialIndex = materialIndex(*pData, primitive.material);
            const cgltf_accessor *pPositionAccessor =
                findAttributeAccessor(primitive, cgltf_attribute_type_position);
            const cgltf_accessor *pNormalAccessor =
                findAttributeAccessor(primitive, cgltf_attribute_type_normal);
            const cgltf_accessor *pTexcoordAccessor =
                findAttributeAccessor(primitive, cgltf_attribute_type_texcoord);
            const cgltf_accessor *pJointAccessor =
                findAttributeAccessor(primitive, cgltf_attribute_type_joints);
            const cgltf_accessor *pWeightAccessor =
                findAttributeAccessor(primitive, cgltf_attribute_type_weights);

            modelPrimitive.hasPositions = pPositionAccessor != nullptr;
            modelPrimitive.hasNormals = pNormalAccessor != nullptr;
            modelPrimitive.hasTexcoords = pTexcoordAccessor != nullptr;
            modelPrimitive.hasJoints = pJointAccessor != nullptr;
            modelPrimitive.hasWeights = pWeightAccessor != nullptr;
            modelPrimitive.vertexCount = pPositionAccessor != nullptr ? pPositionAccessor->count : 0;
            modelPrimitive.indexCount = primitive.indices != nullptr ? primitive.indices->count : 0;
            modelPrimitive.vertices.reserve(modelPrimitive.vertexCount);
            for (cgltf_size vertexIndex = 0; vertexIndex < modelPrimitive.vertexCount; ++vertexIndex)
            {
                AnimatedModelVertex vertex = {};
                vertex.position = vec3FromAccessor(pPositionAccessor, vertexIndex);
                vertex.normal = vec3FromAccessor(pNormalAccessor, vertexIndex);
                vertex.texcoord = vec2FromAccessor(pTexcoordAccessor, vertexIndex);
                vertex.joints = jointsFromAccessor(pJointAccessor, vertexIndex);
                vertex.weights = weightsFromAccessor(pWeightAccessor, vertexIndex);
                modelPrimitive.vertices.push_back(vertex);
                expandBounds(modelPrimitive.bounds, vertex.position);
                expandBounds(asset.bounds, vertex.position);
            }

            modelPrimitive.indices.reserve(modelPrimitive.indexCount);
            for (cgltf_size index = 0; index < modelPrimitive.indexCount; ++index)
            {
                modelPrimitive.indices.push_back(indexFromAccessor(primitive.indices, index));
            }
            asset.primitives.push_back(modelPrimitive);
        }
    }

    asset.skins.reserve(pData->skins_count);
    for (cgltf_size skinIndexValue = 0; skinIndexValue < pData->skins_count; ++skinIndexValue)
    {
        const cgltf_skin &skin = pData->skins[skinIndexValue];
        AnimatedModelSkin modelSkin = {};
        modelSkin.name = stringValue(skin.name);
        modelSkin.joints.reserve(skin.joints_count);
        for (cgltf_size jointIndex = 0; jointIndex < skin.joints_count; ++jointIndex)
        {
            AnimatedModelJoint modelJoint = {};
            modelJoint.nodeIndex = nodeIndex(*pData, skin.joints[jointIndex]);
            modelJoint.inverseBindMatrix =
                skin.inverse_bind_matrices != nullptr
                    ? matrixFromAccessor(*skin.inverse_bind_matrices, jointIndex)
                    : identityMatrix();
            modelSkin.joints.push_back(modelJoint);
        }
        asset.skins.push_back(std::move(modelSkin));
    }

    asset.clips.reserve(pData->animations_count);
    for (cgltf_size animationIndex = 0; animationIndex < pData->animations_count; ++animationIndex)
    {
        const cgltf_animation &animation = pData->animations[animationIndex];
        AnimatedModelClip clip = {};
        clip.name = stringValue(animation.name);
        clip.channels.reserve(animation.channels_count);
        for (cgltf_size channelIndex = 0; channelIndex < animation.channels_count; ++channelIndex)
        {
            const cgltf_animation_channel &channel = animation.channels[channelIndex];
            if (channel.target_node == nullptr || channel.sampler == nullptr)
            {
                continue;
            }

            AnimatedModelChannel modelChannel = {};
            modelChannel.nodeIndex = nodeIndex(*pData, channel.target_node);
            modelChannel.path = channelPath(channel.target_path);
            modelChannel.timesSeconds = readScalarAccessor(channel.sampler->input);
            if (!modelChannel.timesSeconds.empty())
            {
                clip.durationSeconds = std::max(clip.durationSeconds, modelChannel.timesSeconds.back());
            }

            const cgltf_accessor *pOutput = channel.sampler->output;
            if (pOutput != nullptr)
            {
                modelChannel.transforms.reserve(pOutput->count);
                for (cgltf_size sampleIndex = 0; sampleIndex < pOutput->count; ++sampleIndex)
                {
                    modelChannel.transforms.push_back(
                        transformValueAt(pOutput, channel.target_path, sampleIndex));
                }
            }

            clip.channels.push_back(std::move(modelChannel));
        }
        asset.clips.push_back(std::move(clip));
    }

    cgltf_free(pData);
    validateAnimatedModelAsset(asset);
    return asset;
}

void validateAnimatedModelAsset(AnimatedModelAsset &asset)
{
    if (asset.nodes.empty())
    {
        addDiagnostic(asset, true, "animated model has no nodes");
    }
    if (asset.primitives.empty())
    {
        addDiagnostic(asset, true, "animated model has no mesh primitives");
    }
    if (!asset.bounds.valid)
    {
        addDiagnostic(asset, true, "animated model has no valid mesh bounds");
    }
    else if (!boundsAreFinite(asset.bounds))
    {
        addDiagnostic(asset, true, "animated model has non-finite mesh bounds");
    }
    if (asset.skins.empty())
    {
        addDiagnostic(asset, true, "animated model has no skins");
    }
    if (asset.clips.empty())
    {
        addDiagnostic(asset, true, "animated model has no animation clips");
    }
    if (asset.lod.valid)
    {
        if (asset.lod.exportedIndex < 0)
        {
            addDiagnostic(asset, true, "animated model LOD exported index is negative");
        }
        for (const float distance : asset.lod.distances)
        {
            if (!std::isfinite(distance) || distance < 0.0f)
            {
                addDiagnostic(asset, true, "animated model LOD distance is invalid");
            }
        }
    }

    for (size_t nodeIndexValue = 0; nodeIndexValue < asset.nodes.size(); ++nodeIndexValue)
    {
        const AnimatedModelNode &node = asset.nodes[nodeIndexValue];
        if (node.parentIndex >= static_cast<int>(asset.nodes.size()))
        {
            addDiagnostic(asset, true, "animated model node references an invalid parent");
        }
        for (const size_t childIndex : node.childIndices)
        {
            if (childIndex >= asset.nodes.size())
            {
                addDiagnostic(asset, true, "animated model node references an invalid child");
            }
        }
        if (!transformIsFinite(node.bindTransform))
        {
            addDiagnostic(asset, true, "animated model node has a non-finite bind transform");
        }
    }

    for (const AnimatedModelPrimitive &primitive : asset.primitives)
    {
        if (!primitive.hasPositions)
        {
            addDiagnostic(asset, true, "mesh primitive is missing POSITION");
        }
        if (!primitive.hasNormals)
        {
            addDiagnostic(asset, true, "mesh primitive is missing NORMAL");
        }
        if (!primitive.hasTexcoords)
        {
            addDiagnostic(asset, false, "mesh primitive is missing TEXCOORD_0");
        }
        if (!primitive.hasJoints)
        {
            addDiagnostic(asset, true, "mesh primitive is missing JOINTS_0");
        }
        if (!primitive.hasWeights)
        {
            addDiagnostic(asset, true, "mesh primitive is missing WEIGHTS_0");
        }
        if (!primitive.bounds.valid)
        {
            addDiagnostic(asset, true, "mesh primitive has no valid bounds");
        }
        else if (!boundsAreFinite(primitive.bounds))
        {
            addDiagnostic(asset, true, "mesh primitive has non-finite bounds");
        }
        if (primitive.vertexCount != primitive.vertices.size())
        {
            addDiagnostic(asset, true, "mesh primitive vertex data count does not match POSITION count");
        }
        if (primitive.indexCount != primitive.indices.size())
        {
            addDiagnostic(asset, true, "mesh primitive index data count does not match index accessor count");
        }
        if (primitive.hasNormals && primitive.vertices.size() != primitive.vertexCount)
        {
            addDiagnostic(asset, true, "mesh primitive NORMAL count does not match POSITION count");
        }
        if (primitive.hasTexcoords && primitive.vertices.size() != primitive.vertexCount)
        {
            addDiagnostic(asset, true, "mesh primitive TEXCOORD_0 count does not match POSITION count");
        }

        for (const AnimatedModelVertex &vertex : primitive.vertices)
        {
            if (!std::isfinite(vertex.position.x) || !std::isfinite(vertex.position.y)
                || !std::isfinite(vertex.position.z))
            {
                addDiagnostic(asset, true, "mesh primitive has a non-finite POSITION value");
            }
            if (!std::isfinite(vertex.normal.x) || !std::isfinite(vertex.normal.y)
                || !std::isfinite(vertex.normal.z))
            {
                addDiagnostic(asset, true, "mesh primitive has a non-finite NORMAL value");
            }
            if (!std::isfinite(vertex.texcoord[0]) || !std::isfinite(vertex.texcoord[1]))
            {
                addDiagnostic(asset, true, "mesh primitive has a non-finite TEXCOORD_0 value");
            }
            for (const float weight : vertex.weights)
            {
                if (!std::isfinite(weight))
                {
                    addDiagnostic(asset, true, "mesh primitive has a non-finite WEIGHTS_0 value");
                }
            }
        }

        for (const uint32_t index : primitive.indices)
        {
            if (index >= primitive.vertexCount)
            {
                addDiagnostic(asset, true, "mesh primitive index references a missing vertex");
            }
        }

        if (!asset.skins.empty())
        {
            const size_t jointCount = asset.skins.front().joints.size();
            for (const AnimatedModelVertex &vertex : primitive.vertices)
            {
                for (size_t jointIndex = 0; jointIndex < vertex.joints.size(); ++jointIndex)
                {
                    if (vertex.weights[jointIndex] > 0.0f && vertex.joints[jointIndex] >= jointCount)
                    {
                        addDiagnostic(asset, true, "mesh primitive JOINTS_0 value references a missing joint");
                    }
                }
            }
        }
    }

    for (const AnimatedModelSkin &skin : asset.skins)
    {
        for (const AnimatedModelJoint &joint : skin.joints)
        {
            if (joint.nodeIndex >= asset.nodes.size())
            {
                addDiagnostic(asset, true, "skin joint references an invalid node");
            }
            if (!animatedModelMatrixIsFinite(joint.inverseBindMatrix))
            {
                addDiagnostic(asset, true, "skin joint has a non-finite inverse bind matrix");
            }
        }
    }

    for (const AnimatedModelClip &clip : asset.clips)
    {
        if (!std::isfinite(clip.durationSeconds) || clip.durationSeconds < 0.0f)
        {
            addDiagnostic(asset, true, "animation clip has an invalid duration");
        }
        for (const AnimatedModelChannel &channel : clip.channels)
        {
            if (channel.nodeIndex >= asset.nodes.size())
            {
                addDiagnostic(asset, true, "animation channel references an invalid node");
            }
            if (channel.timesSeconds.size() != channel.transforms.size())
            {
                addDiagnostic(asset, true, "animation channel input/output sample counts differ");
            }
            if (channel.path == AnimatedModelChannelPath::Unsupported)
            {
                addDiagnostic(asset, false, "animation channel uses an unsupported path");
            }
            for (size_t timeIndex = 0; timeIndex < channel.timesSeconds.size(); ++timeIndex)
            {
                const float timeSeconds = channel.timesSeconds[timeIndex];
                if (!std::isfinite(timeSeconds) || timeSeconds < 0.0f)
                {
                    addDiagnostic(asset, true, "animation channel has an invalid key time");
                }
                if (timeIndex > 0 && timeSeconds < channel.timesSeconds[timeIndex - 1])
                {
                    addDiagnostic(asset, true, "animation channel key times are not monotonic");
                }
            }
            for (const AnimatedModelTransform &transform : channel.transforms)
            {
                if (!transformIsFinite(transform))
                {
                    addDiagnostic(asset, true, "animation channel has a non-finite key transform");
                }
            }
        }
    }
}

AnimatedModelPose sampleAnimatedModelPose(
    const AnimatedModelAsset &asset,
    const AnimatedModelClip *pClip,
    float timeSeconds,
    bool loop)
{
    return poseFromLocalTransforms(asset, sampleLocalTransforms(asset, pClip, timeSeconds, loop));
}

std::vector<AnimatedModelEvent> animatedModelEventsInInterval(
    const AnimatedModelClip &clip,
    float startSeconds,
    float endSeconds,
    bool loop)
{
    std::vector<AnimatedModelEvent> events;
    if (clip.events.empty() || endSeconds <= startSeconds)
    {
        return events;
    }

    if (clip.durationSeconds <= 0.0f)
    {
        appendEventsInNormalizedInterval(clip, startSeconds, endSeconds, false, events);
        return events;
    }

    if (!loop)
    {
        const float start = std::clamp(startSeconds, 0.0f, clip.durationSeconds);
        const float end = std::clamp(endSeconds, 0.0f, clip.durationSeconds);
        appendEventsInNormalizedInterval(clip, start, end, false, events);
        return events;
    }

    float cursor = startSeconds;
    size_t guard = 0;
    while (cursor < endSeconds && guard < 10000)
    {
        ++guard;
        const float normalizedStart = normalizeSampleTime(cursor, clip.durationSeconds, true);
        const float segmentEnd = std::min(endSeconds, cursor + (clip.durationSeconds - normalizedStart));
        const bool wrapsAtSegmentEnd = segmentEnd < endSeconds;
        const float normalizedEnd = wrapsAtSegmentEnd
            ? clip.durationSeconds
            : normalizeSampleTime(segmentEnd, clip.durationSeconds, true);

        appendEventsInNormalizedInterval(clip, normalizedStart, normalizedEnd, false, events);
        cursor = segmentEnd;

        if (wrapsAtSegmentEnd)
        {
            appendEventsInNormalizedInterval(clip, 0.0f, 0.0f, true, events);
        }

        if (segmentEnd == cursor && !wrapsAtSegmentEnd)
        {
            break;
        }
    }

    return events;
}

void animatedModelControllerPlay(
    AnimatedModelController &controller,
    const AnimatedModelClip *pClip,
    bool loop,
    float transitionDurationSeconds)
{
    controller.pPreviousClip = controller.pCurrentClip != pClip ? controller.pCurrentClip : nullptr;
    controller.previousTimeSeconds = controller.currentTimeSeconds;
    controller.previousLoop = controller.loop;
    controller.pCurrentClip = pClip;
    controller.currentTimeSeconds = 0.0f;
    controller.loop = loop;
    controller.transitionDurationSeconds = std::max(0.0f, transitionDurationSeconds);
    controller.transitionElapsedSeconds = 0.0f;
    if (controller.pPreviousClip == nullptr)
    {
        controller.transitionDurationSeconds = 0.0f;
    }
}

AnimatedModelControllerUpdate animatedModelControllerUpdate(
    AnimatedModelController &controller,
    float deltaSeconds)
{
    AnimatedModelControllerUpdate result = {};
    if (controller.pCurrentClip == nullptr || deltaSeconds <= 0.0f || controller.rate <= 0.0f)
    {
        return result;
    }

    const float startTime = controller.currentTimeSeconds;
    const float endTime = startTime + deltaSeconds * controller.rate;
    result.events = animatedModelEventsInInterval(*controller.pCurrentClip, startTime, endTime, controller.loop);

    if (controller.pPreviousClip != nullptr)
    {
        const float previousEndTime = controller.previousTimeSeconds + deltaSeconds * controller.rate;
        controller.previousTimeSeconds =
            normalizeSampleTime(previousEndTime, controller.pPreviousClip->durationSeconds, controller.previousLoop);
    }

    if (controller.loop)
    {
        controller.currentTimeSeconds =
            normalizeSampleTime(endTime, controller.pCurrentClip->durationSeconds, true);
    }
    else
    {
        controller.currentTimeSeconds =
            normalizeSampleTime(endTime, controller.pCurrentClip->durationSeconds, false);
        result.clipFinished = endTime >= controller.pCurrentClip->durationSeconds;
    }

    if (controller.transitionDurationSeconds > 0.0f)
    {
        controller.transitionElapsedSeconds =
            std::min(controller.transitionElapsedSeconds + deltaSeconds, controller.transitionDurationSeconds);
        if (controller.transitionElapsedSeconds >= controller.transitionDurationSeconds)
        {
            controller.pPreviousClip = nullptr;
            controller.previousTimeSeconds = 0.0f;
            controller.transitionDurationSeconds = 0.0f;
            controller.transitionElapsedSeconds = 0.0f;
        }
    }

    return result;
}

AnimatedModelPose sampleAnimatedModelControllerPose(
    const AnimatedModelAsset &asset,
    const AnimatedModelController &controller)
{
    if (controller.pCurrentClip == nullptr)
    {
        return sampleAnimatedModelPose(asset, nullptr, 0.0f, true);
    }

    std::vector<AnimatedModelTransform> currentTransforms = sampleLocalTransforms(
        asset,
        controller.pCurrentClip,
        controller.currentTimeSeconds,
        controller.loop);

    if (controller.pPreviousClip == nullptr || controller.transitionDurationSeconds <= 0.0f)
    {
        return poseFromLocalTransforms(asset, std::move(currentTransforms));
    }

    std::vector<AnimatedModelTransform> previousTransforms = sampleLocalTransforms(
        asset,
        controller.pPreviousClip,
        controller.previousTimeSeconds,
        controller.previousLoop);
    const float amount = std::clamp(
        controller.transitionElapsedSeconds / controller.transitionDurationSeconds,
        0.0f,
        1.0f);

    const size_t blendCount = std::min(previousTransforms.size(), currentTransforms.size());
    for (size_t index = 0; index < blendCount; ++index)
    {
        currentTransforms[index] = blendTransform(previousTransforms[index], currentTransforms[index], amount);
    }

    return poseFromLocalTransforms(asset, std::move(currentTransforms));
}

AnimatedModelRenderPrep buildAnimatedModelRenderPrep(
    const AnimatedModelAsset &asset,
    const AnimatedModelPose &pose,
    size_t maxBoneMatrices)
{
    AnimatedModelRenderPrep result = {};
    if (maxBoneMatrices == 0)
    {
        result.diagnostics.push_back(AnimatedModelDiagnostic{
            .message = "animated model render prep max bone matrix count is zero",
            .error = true,
        });
        return result;
    }

    for (size_t primitiveIndex = 0; primitiveIndex < asset.primitives.size(); ++primitiveIndex)
    {
        const AnimatedModelPrimitive &primitive = asset.primitives[primitiveIndex];
        std::vector<uint32_t> sourceJoints;
        bool rejected = false;

        for (const AnimatedModelVertex &vertex : primitive.vertices)
        {
            if (rejected)
            {
                break;
            }

            for (size_t slot = 0; slot < vertex.joints.size(); ++slot)
            {
                if (rejected)
                {
                    break;
                }

                if (vertex.weights[slot] <= 0.0f)
                {
                    continue;
                }

                const uint32_t sourceJoint = vertex.joints[slot];
                if (sourceJoint >= pose.skinningMatrices.size())
                {
                    result.diagnostics.push_back(AnimatedModelDiagnostic{
                        .message = "animated model draw primitive references a missing skinning matrix",
                        .error = true,
                    });
                    rejected = true;
                    continue;
                }

                if (std::find(sourceJoints.begin(), sourceJoints.end(), sourceJoint) == sourceJoints.end())
                {
                    sourceJoints.push_back(sourceJoint);
                    if (sourceJoints.size() > maxBoneMatrices)
                    {
                        result.diagnostics.push_back(AnimatedModelDiagnostic{
                            .message = "animated model draw primitive exceeds bone palette limit",
                            .error = true,
                        });
                        rejected = true;
                    }
                }
            }
        }

        if (rejected)
        {
            continue;
        }

        AnimatedModelDrawItem drawItem = {};
        drawItem.primitiveIndex = primitiveIndex;
        drawItem.materialIndex = primitive.materialIndex;
        drawItem.vertices = primitive.vertices;
        drawItem.indices = primitive.indices;
        drawItem.bounds = primitive.bounds;

        drawItem.bonePalette.reserve(sourceJoints.size());
        for (const uint32_t sourceJoint : sourceJoints)
        {
            drawItem.bonePalette.push_back(pose.skinningMatrices[sourceJoint]);
        }

        for (AnimatedModelVertex &vertex : drawItem.vertices)
        {
            for (size_t slot = 0; slot < vertex.joints.size(); ++slot)
            {
                if (vertex.weights[slot] <= 0.0f)
                {
                    vertex.joints[slot] = 0;
                    continue;
                }

                const uint32_t sourceJoint = vertex.joints[slot];
                const std::vector<uint32_t>::const_iterator iterator =
                    std::find(sourceJoints.begin(), sourceJoints.end(), sourceJoint);
                vertex.joints[slot] = iterator != sourceJoints.end()
                    ? static_cast<uint32_t>(iterator - sourceJoints.begin())
                    : 0;
            }
        }

        if (primitive.materialIndex < asset.materials.size())
        {
            const AnimatedModelMaterial &material = asset.materials[primitive.materialIndex];
            drawItem.texture = material.baseColorTextureUri;
            drawItem.alphaMask = material.alphaMask;
            drawItem.alphaBlend = material.alphaBlend;
            drawItem.doubleSided = material.doubleSided;
        }

        result.counters.skinnedDrawCalls += 1;
        result.counters.skinnedTriangles += drawItem.indices.size() / 3;
        result.counters.uploadedBoneMatrices += drawItem.bonePalette.size();
        if (!result.drawItems.empty()
            && result.drawItems.back().materialIndex != drawItem.materialIndex)
        {
            result.counters.materialSwitches += 1;
        }

        result.drawItems.push_back(std::move(drawItem));
    }

    return result;
}

std::optional<AnimatedModelMat4> animatedModelSocketTransform(
    const AnimatedModelAsset &asset,
    const AnimatedModelPose &pose,
    std::string_view socketName)
{
    const std::optional<size_t> socketIndex = asset.findSocketIndex(socketName);
    if (!socketIndex)
    {
        return std::nullopt;
    }

    const AnimatedModelSocket &socket = asset.sockets[*socketIndex];
    if (socket.nodeIndex >= pose.globalTransforms.size())
    {
        return std::nullopt;
    }

    return multiplyMatrix(pose.globalTransforms[socket.nodeIndex], matrixFromTransform(socket.localTransform));
}

bool animatedModelMatrixIsFinite(const AnimatedModelMat4 &matrix)
{
    for (float value : matrix.values)
    {
        if (!std::isfinite(value))
        {
            return false;
        }
    }
    return true;
}
}
