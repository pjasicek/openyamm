#pragma once

#include "engine/models/ModelAsset.h"

#include <vector>

namespace OpenYAMM::Engine
{
struct ModelPose
{
    std::vector<ModelTransform> localTransforms;
    std::vector<ModelMatrix> localMatrices;
    std::vector<ModelMatrix> globalMatrices;
    std::vector<std::vector<float>> morphWeights;
    // Node/primitive vertices: world space for skins, mesh-local space for unskinned morphs.
    std::vector<std::vector<std::vector<ModelVertex>>> deformedVertices;
    uint64_t deformationRevision = 0;
    uint64_t matrixRevision = 0;
};

// Mesh-local bounds per influencing joint (one entry for an unskinned mesh).
// Keeping morph deltas separate permits arbitrary animated weights, including negative weights.
struct ModelJointBounds
{
    ModelBounds base;
    std::vector<ModelBounds> morphs;
};
struct ModelDeformationBounds
{
    std::vector<std::vector<ModelJointBounds>> nodes;
    float motionRadius = -1;
};

ModelDeformationBounds buildModelDeformationBounds(const ModelAsset &asset);
ModelBounds modelPoseBounds(const ModelAsset &asset, const ModelPose &pose, const ModelDeformationBounds &bounds);
ModelBounds modelExactPoseBounds(const ModelAsset &asset, const ModelPose &pose);

void resetModelPose(const ModelAsset &asset, ModelPose &pose);
void evaluateModelClip(const ModelAsset &asset, uint32_t clipIndex, float timeSeconds, ModelPose &pose);
void evaluateModelHierarchy(const ModelAsset &asset, const ModelMatrix &rootMatrix, ModelPose &pose);
void deformModelPose(const ModelAsset &asset, ModelPose &pose, bool deformSkins = true);
}
