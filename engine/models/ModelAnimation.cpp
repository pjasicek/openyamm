#include "engine/models/ModelAnimation.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Engine
{
namespace
{
void includePoint(ModelBounds &bounds, const std::array<float, 3> &point)
{
    if (!bounds.valid)
    {
        bounds = {point, point, true};
    }
    for (size_t axis = 0; axis < 3; ++axis)
    {
        bounds.min[axis] = std::min(bounds.min[axis], point[axis]);
        bounds.max[axis] = std::max(bounds.max[axis], point[axis]);
    }
}

std::array<float, 3> morphPosition(const ModelPrimitive &primitive, const std::vector<float> &weights,
    size_t vertexIndex)
{
    std::array<float, 3> position = primitive.vertices[vertexIndex].position;
    for (size_t targetIndex = 0; targetIndex < primitive.morphTargets.size(); ++targetIndex)
    {
        const ModelMorphTarget &target = primitive.morphTargets[targetIndex];
        if (weights[targetIndex] == 0.0f || target.positions.empty())
        {
            continue;
        }
        for (size_t axis = 0; axis < 3; ++axis)
        {
            position[axis] += weights[targetIndex] * target.positions[vertexIndex][axis];
        }
    }
    return position;
}

std::array<float, 3> skinPosition(const std::array<float, 3> &position, const ModelVertexInfluences &influences,
    const std::vector<ModelMatrix> &joints)
{
    std::array<float, 3> result = {};
    for (size_t i = 0; i < influences.weights.size(); ++i)
    {
        const float weight = influences.weights[i];
        if (weight == 0.0f)
        {
            continue;
        }
        const ModelMatrix &joint = joints[influences.joints[i]];
        for (size_t axis = 0; axis < 3; ++axis)
        {
            result[axis] += weight * (joint[axis] * position[0] + joint[4 + axis] * position[1]
                + joint[8 + axis] * position[2] + joint[12 + axis]);
        }
    }
    return result;
}

std::array<float, 4> normalizedQuaternion(const std::array<float, 4> &value)
{
    const float length = std::sqrt(
        value[0] * value[0] + value[1] * value[1] + value[2] * value[2] + value[3] * value[3]);
    if (length <= 0.0f)
    {
        return {0.0f, 0.0f, 0.0f, 1.0f};
    }
    return {value[0] / length, value[1] / length, value[2] / length, value[3] / length};
}

std::array<float, 4> interpolateQuaternion(
    const std::array<float, 4> &leftValue,
    const std::array<float, 4> &rightValue,
    float amount
)
{
    std::array<float, 4> left = normalizedQuaternion(leftValue);
    std::array<float, 4> right = normalizedQuaternion(rightValue);
    float dot = left[0] * right[0] + left[1] * right[1] + left[2] * right[2] + left[3] * right[3];
    if (dot < 0.0f)
    {
        dot = -dot;
        for (float &component : right)
        {
            component = -component;
        }
    }
    dot = std::clamp(dot, -1.0f, 1.0f);
    if (dot > 0.9995f)
    {
        std::array<float, 4> result = {};
        for (size_t component = 0; component < result.size(); ++component)
        {
            result[component] = left[component] + (right[component] - left[component]) * amount;
        }
        return normalizedQuaternion(result);
    }

    const float angle = std::acos(dot);
    const float denominator = std::sin(angle);
    const float leftWeight = std::sin((1.0f - amount) * angle) / denominator;
    const float rightWeight = std::sin(amount * angle) / denominator;
    std::array<float, 4> result = {};
    for (size_t component = 0; component < result.size(); ++component)
    {
        result[component] = left[component] * leftWeight + right[component] * rightWeight;
    }
    return normalizedQuaternion(result);
}

// Keyframe rotations are close together: normalized lerp matches slerp within a fraction of a degree, without
// acos/sin per channel. Pose blends keep interpolateQuaternion.
std::array<float, 4> nlerpQuaternion(const std::array<float, 4> &left, const std::array<float, 4> &right, float amount)
{
    const float dot = left[0] * right[0] + left[1] * right[1] + left[2] * right[2] + left[3] * right[3];
    const float sign = dot < 0.0f ? -1.0f : 1.0f;
    std::array<float, 4> result = {};
    for (size_t component = 0; component < result.size(); ++component)
    {
        result[component] = left[component] + (right[component] * sign - left[component]) * amount;
    }
    return normalizedQuaternion(result);
}

void sampleChannel(const ModelAnimationChannel &channel, float timeSeconds, ModelTransform &transform,
    std::vector<float> &weights)
{
    size_t rightIndex =
        std::upper_bound(channel.times.begin(), channel.times.end(), timeSeconds) - channel.times.begin();
    const size_t leftIndex = rightIndex == 0 ? 0 : rightIndex - 1;
    rightIndex = std::min(rightIndex, channel.times.size() - 1);
    float amount = 0.0f;
    if (channel.interpolation == ModelAnimationInterpolation::Linear && rightIndex != leftIndex)
    {
        const float interval = channel.times[rightIndex] - channel.times[leftIndex];
        amount = interval > 0.0f ? (timeSeconds - channel.times[leftIndex]) / interval : 0.0f;
        amount = std::clamp(amount, 0.0f, 1.0f);
    }

    if (channel.target == ModelAnimationTarget::Weights)
    {
        for (size_t i = 0; i < weights.size(); ++i)
        {
            weights[i] = channel.weightValues[leftIndex][i]
                + (channel.weightValues[rightIndex][i] - channel.weightValues[leftIndex][i]) * amount;
        }
        return;
    }
    const std::array<float, 4> &left = channel.values[leftIndex];
    const std::array<float, 4> &right = channel.values[rightIndex];
    if (channel.target == ModelAnimationTarget::Rotation)
    {
        transform.rotation = channel.interpolation == ModelAnimationInterpolation::Step
            ? normalizedQuaternion(left) : nlerpQuaternion(left, right, amount);
        return;
    }

    std::array<float, 3> *pOutput = channel.target == ModelAnimationTarget::Translation
        ? &transform.translation : &transform.scale;
    for (size_t component = 0; component < 3; ++component)
    {
        (*pOutput)[component] = left[component] + (right[component] - left[component]) * amount;
    }
}
}

ModelDeformationBounds buildModelDeformationBounds(const ModelAsset &asset)
{
    ModelDeformationBounds result;
    result.nodes.resize(asset.nodes.size());
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        if (node.meshIndex < 0)
        {
            continue;
        }
        std::vector<ModelJointBounds> &bounds = result.nodes[nodeIndex];
        bounds.resize(node.skinIndex >= 0 ? asset.skins[node.skinIndex].joints.size() : 1);
        for (ModelJointBounds &joint : bounds)
        {
            joint.morphs.resize(node.weights.size());
        }
        for (const ModelPrimitive &primitive : asset.meshes[node.meshIndex].primitives)
        {
            for (size_t vertex = 0; vertex < primitive.vertices.size(); ++vertex)
            {
                const size_t count = node.skinIndex >= 0 ? primitive.influences[vertex].weights.size() : 1;
                for (size_t influence = 0; influence < count; ++influence)
                {
                    if (node.skinIndex >= 0 && primitive.influences[vertex].weights[influence] == 0)
                    {
                        continue;
                    }
                    ModelJointBounds &joint = bounds[node.skinIndex >= 0
                        ? primitive.influences[vertex].joints[influence] : 0];
                    includePoint(joint.base, primitive.vertices[vertex].position);
                    for (size_t target = 0; target < primitive.morphTargets.size(); ++target)
                    {
                        const std::vector<std::array<float, 3>> &positions = primitive.morphTargets[target].positions;
                        includePoint(joint.morphs[target],
                            positions.empty() ? std::array<float, 3>{} : positions[vertex]);
                    }
                }
            }
        }
    }
    // Bound all possible interpolation times, rather than sampling frames and missing an intermediate rotation.
    // Translation lengths and absolute scales compose along the hierarchy; rotation preserves lengths.
    std::vector<float> offsets(asset.nodes.size()), scales(asset.nodes.size());
    std::vector<std::vector<float>> morphLimits(asset.nodes.size());
    const auto length = [](const std::array<float, 3> &point)
    {
        return std::sqrt(point[0] * point[0] + point[1] * point[1] + point[2] * point[2]);
    };
    for (size_t index = 0; index < asset.nodes.size(); ++index)
    {
        const ModelNode &node = asset.nodes[index];
        offsets[index] = length(node.transform.translation);
        scales[index] = std::max({std::abs(node.transform.scale[0]),
            std::abs(node.transform.scale[1]), std::abs(node.transform.scale[2])});
        if (node.usesMatrix)
        {
            offsets[index] = length({node.matrix[12], node.matrix[13], node.matrix[14]});
            float squared = 0;
            for (size_t column = 0; column < 3; ++column)
            {
                for (size_t row = 0; row < 3; ++row)
                {
                    squared += node.matrix[column * 4 + row] * node.matrix[column * 4 + row];
                }
            }
            scales[index] = std::sqrt(squared); // Conservative operator norm, including authored shear.
        }
        morphLimits[index] = node.weights;
        for (float &weight : morphLimits[index])
        {
            weight = std::abs(weight);
        }
    }
    for (const ModelAnimationClip &clip : asset.clips)
    {
        for (const ModelAnimationChannel &channel : clip.channels)
        {
            for (const std::array<float, 4> &value : channel.values)
            {
                if (channel.target == ModelAnimationTarget::Translation)
                {
                    offsets[channel.nodeIndex] = std::max(offsets[channel.nodeIndex],
                        length({value[0], value[1], value[2]}));
                }
                else if (channel.target == ModelAnimationTarget::Scale)
                {
                    scales[channel.nodeIndex] = std::max({scales[channel.nodeIndex],
                        std::abs(value[0]), std::abs(value[1]), std::abs(value[2])});
                }
            }
            for (const std::vector<float> &weights : channel.weightValues)
            {
                for (size_t index = 0; index < weights.size(); ++index)
                {
                    morphLimits[channel.nodeIndex][index] = std::max(
                        morphLimits[channel.nodeIndex][index], std::abs(weights[index]));
                }
            }
        }
    }
    for (uint32_t index : asset.hierarchyOrder)
    {
        const int parent = asset.nodes[index].parentIndex;
        if (parent >= 0)
        {
            offsets[index] = offsets[parent] + scales[parent] * offsets[index];
            scales[index] *= scales[parent];
        }
    }
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        for (size_t jointIndex = 0; jointIndex < result.nodes[nodeIndex].size(); ++jointIndex)
        {
            const ModelJointBounds &joint = result.nodes[nodeIndex][jointIndex];
            if (!joint.base.valid)
            {
                continue;
            }
            ModelBounds local = joint.base;
            for (size_t target = 0; target < joint.morphs.size(); ++target)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    const float delta = morphLimits[nodeIndex][target]
                        * std::max(std::abs(joint.morphs[target].min[axis]), std::abs(joint.morphs[target].max[axis]));
                    local.min[axis] -= delta;
                    local.max[axis] += delta;
                }
            }
            const uint32_t index = node.skinIndex >= 0 ? asset.skins[node.skinIndex].joints[jointIndex] : nodeIndex;
            const ModelMatrix matrix = node.skinIndex >= 0
                ? asset.skins[node.skinIndex].inverseBindMatrices[jointIndex] : identityModelMatrix();
            for (uint32_t corner = 0; corner < 8; ++corner)
            {
                const float point[3] = {corner & 1 ? local.max[0] : local.min[0],
                    corner & 2 ? local.max[1] : local.min[1], corner & 4 ? local.max[2] : local.min[2]};
                const float radius = length({matrix[0] * point[0] + matrix[4] * point[1]
                        + matrix[8] * point[2] + matrix[12],
                    matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
                    matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14]});
                result.motionRadius = std::max(result.motionRadius, offsets[index] + scales[index] * radius);
            }
        }
    }
    return result;
}

ModelBounds modelPoseBounds(const ModelAsset &asset, const ModelPose &pose, const ModelDeformationBounds &bounds)
{
    ModelBounds result;
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        if (node.meshIndex < 0 || !modelMatrixVisible(pose.globalMatrices[nodeIndex]))
        {
            continue;
        }
        for (size_t jointIndex = 0; jointIndex < bounds.nodes[nodeIndex].size(); ++jointIndex)
        {
            const ModelJointBounds &joint = bounds.nodes[nodeIndex][jointIndex];
            ModelBounds local = joint.base;
            if (!local.valid)
            {
                continue;
            }
            for (size_t target = 0; target < joint.morphs.size(); ++target)
            {
                const float weight = pose.morphWeights[nodeIndex][target];
                const ModelBounds &delta = joint.morphs[target];
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    local.min[axis] += weight * (weight >= 0 ? delta.min[axis] : delta.max[axis]);
                    local.max[axis] += weight * (weight >= 0 ? delta.max[axis] : delta.min[axis]);
                }
            }
            const ModelMatrix matrix = node.skinIndex >= 0
                ? multiplyModelMatrices(pose.globalMatrices[asset.skins[node.skinIndex].joints[jointIndex]],
                    asset.skins[node.skinIndex].inverseBindMatrices[jointIndex])
                : pose.globalMatrices[nodeIndex];
            for (uint32_t corner = 0; corner < 8; ++corner)
            {
                const float point[3] = {corner & 1 ? local.max[0] : local.min[0],
                    corner & 2 ? local.max[1] : local.min[1], corner & 4 ? local.max[2] : local.min[2]};
                includePoint(result, {matrix[0] * point[0] + matrix[4] * point[1]
                        + matrix[8] * point[2] + matrix[12],
                    matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
                    matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14]});
            }
        }
    }
    return result;
}

ModelBounds modelExactPoseBounds(const ModelAsset &asset, const ModelPose &pose, bool coarsestLod)
{
    ModelBounds result;
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        const ModelMatrix &matrix = pose.globalMatrices[nodeIndex];
        if (node.meshIndex < 0 || !modelMatrixVisible(matrix))
        {
            continue;
        }
        std::vector<ModelMatrix> joints;
        if (node.skinIndex >= 0)
        {
            const ModelSkin &skin = asset.skins[node.skinIndex];
            joints.reserve(skin.joints.size());
            for (size_t i = 0; i < skin.joints.size(); ++i)
            {
                joints.push_back(multiplyModelMatrices(
                    pose.globalMatrices[skin.joints[i]], skin.inverseBindMatrices[i]));
            }
        }
        const ModelMesh &base = asset.meshes[node.meshIndex];
        const ModelMesh &mesh = coarsestLod && !base.lodMeshes.empty() ? asset.meshes[base.lodMeshes.back()] : base;
        for (const ModelPrimitive &primitive : mesh.primitives)
        {
            for (size_t vertexIndex = 0; vertexIndex < primitive.vertices.size(); ++vertexIndex)
            {
                const std::array<float, 3> position =
                    morphPosition(primitive, pose.morphWeights[nodeIndex], vertexIndex);
                if (node.skinIndex >= 0)
                {
                    includePoint(result, skinPosition(position, primitive.influences[vertexIndex], joints));
                }
                else
                {
                    includePoint(result, {
                        matrix[0] * position[0] + matrix[4] * position[1] + matrix[8] * position[2] + matrix[12],
                        matrix[1] * position[0] + matrix[5] * position[1] + matrix[9] * position[2] + matrix[13],
                        matrix[2] * position[0] + matrix[6] * position[1] + matrix[10] * position[2] + matrix[14]});
                }
            }
        }
    }
    return result;
}

void resetModelPose(const ModelAsset &asset, ModelPose &pose)
{
    pose.localTransforms.resize(asset.nodes.size());
    pose.localMatrices.resize(asset.nodes.size());
    pose.globalMatrices.resize(asset.nodes.size());
    pose.morphWeights.resize(asset.nodes.size());
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        pose.localTransforms[nodeIndex] = node.transform;
        pose.localMatrices[nodeIndex] = node.matrix;
        pose.globalMatrices[nodeIndex] = identityModelMatrix();
        pose.morphWeights[nodeIndex] = node.weights;
    }
}

void evaluateModelClip(const ModelAsset &asset, uint32_t clipIndex, float timeSeconds, ModelPose &pose)
{
    resetModelPose(asset, pose);
    if (clipIndex >= asset.clips.size())
    {
        return;
    }
    const ModelAnimationClip &clip = asset.clips[clipIndex];
    for (const ModelAnimationChannel &channel : clip.channels)
    {
        sampleChannel(channel, timeSeconds, pose.localTransforms[channel.nodeIndex],
            pose.morphWeights[channel.nodeIndex]);
    }
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        if (!asset.nodes[nodeIndex].usesMatrix)
        {
            pose.localMatrices[nodeIndex] = composeModelTransform(pose.localTransforms[nodeIndex]);
        }
    }
}

void blendModelPose(const ModelAsset &asset, ModelPose &pose, const ModelPose &other, float amount,
    const std::vector<float> &mask)
{
    for (size_t i = 0; i < asset.nodes.size(); ++i)
    {
        const float weight = amount * (mask.empty() ? 1.0f : mask[i]);
        if (weight <= 0.0f || asset.nodes[i].usesMatrix)
        {
            continue;
        }
        ModelTransform &transform = pose.localTransforms[i];
        const ModelTransform &target = other.localTransforms[i];
        for (size_t axis = 0; axis < 3; ++axis)
        {
            transform.translation[axis] += (target.translation[axis] - transform.translation[axis]) * weight;
            transform.scale[axis] += (target.scale[axis] - transform.scale[axis]) * weight;
        }
        transform.rotation = interpolateQuaternion(transform.rotation, target.rotation, weight);
        for (size_t morph = 0; morph < pose.morphWeights[i].size(); ++morph)
        {
            pose.morphWeights[i][morph] += (other.morphWeights[i][morph] - pose.morphWeights[i][morph]) * weight;
        }
        pose.localMatrices[i] = composeModelTransform(transform);
    }
}

void evaluateModelHierarchy(const ModelAsset &asset, const ModelMatrix &rootMatrix, ModelPose &pose)
{
    for (uint32_t nodeIndex : asset.hierarchyOrder)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        pose.globalMatrices[nodeIndex] = node.parentIndex >= 0
            ? multiplyModelMatrices(pose.globalMatrices[node.parentIndex], pose.localMatrices[nodeIndex])
            : multiplyModelMatrices(rootMatrix, pose.localMatrices[nodeIndex]);
    }
}

void deformModelPose(const ModelAsset &asset, ModelPose &pose, bool deformSkins)
{
    // Full CPU vertices remain available to geometry consumers; picking evaluates positions only.
    // ponytail: morphs use CPU deformation; move them to the GPU if large morph crowds become a measured cost.
    ++pose.deformationRevision;
    pose.deformedVertices.resize(asset.nodes.size());
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        if (node.meshIndex < 0)
        {
            continue;
        }
        const ModelMesh &mesh = asset.meshes[node.meshIndex];
        std::vector<ModelMatrix> joints, normals;
        if (node.skinIndex >= 0 && (deformSkins || !node.weights.empty()))
        {
            const ModelSkin &skin = asset.skins[node.skinIndex];
            for (size_t i = 0; i < skin.joints.size(); ++i)
            {
                joints.push_back(multiplyModelMatrices(
                    pose.globalMatrices[skin.joints[i]], skin.inverseBindMatrices[i]));
                normals.push_back(modelNormalMatrix(joints.back()));
            }
        }
        pose.deformedVertices[nodeIndex].resize(mesh.primitives.size());
        for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
        {
            const ModelPrimitive &primitive = mesh.primitives[primitiveIndex];
            if (primitive.morphTargets.empty() && (node.skinIndex < 0 || !deformSkins))
            {
                continue;
            }
            std::vector<ModelVertex> &vertices = pose.deformedVertices[nodeIndex][primitiveIndex];
            if (!modelMatrixVisible(pose.globalMatrices[nodeIndex]))
            {
                vertices.clear();
                continue;
            }
            vertices = primitive.vertices;
            for (size_t vertexIndex = 0; vertexIndex < vertices.size(); ++vertexIndex)
            {
                ModelVertex &vertex = vertices[vertexIndex];
                vertex.position = morphPosition(primitive, pose.morphWeights[nodeIndex], vertexIndex);
                for (size_t targetIndex = 0; targetIndex < primitive.morphTargets.size(); ++targetIndex)
                {
                    const float weight = pose.morphWeights[nodeIndex][targetIndex];
                    if (weight == 0.0f)
                    {
                        continue;
                    }
                    const ModelMorphTarget &target = primitive.morphTargets[targetIndex];
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        if (!target.normals.empty())
                        {
                            vertex.normal[axis] += weight * target.normals[vertexIndex][axis];
                        }
                    }
                }
                if (node.skinIndex >= 0)
                {
                    const ModelVertexInfluences &influences = primitive.influences[vertexIndex];
                    const ModelVertex original = vertex;
                    vertex.position = skinPosition(original.position, influences, joints);
                    vertex.normal = {};
                    for (size_t i = 0; i < influences.weights.size(); ++i)
                    {
                        const float weight = influences.weights[i];
                        if (weight == 0.0f)
                        {
                            continue;
                        }
                        const ModelMatrix &normal = normals[influences.joints[i]];
                        for (size_t axis = 0; axis < 3; ++axis)
                        {
                            vertex.normal[axis] += weight * (normal[axis] * original.normal[0]
                                + normal[4 + axis] * original.normal[1] + normal[8 + axis] * original.normal[2]);
                        }
                    }
                }
                const float length = std::sqrt(vertex.normal[0] * vertex.normal[0]
                    + vertex.normal[1] * vertex.normal[1] + vertex.normal[2] * vertex.normal[2]);
                if (length > 0.0f)
                {
                    for (float &component : vertex.normal)
                    {
                        component /= length;
                    }
                }
            }
        }
    }
}
}
