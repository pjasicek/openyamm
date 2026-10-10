#include "engine/models/ModelInstance.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace OpenYAMM::Engine
{
namespace
{
void expandBounds(ModelBounds &bounds, const ModelMatrix &matrix, const std::array<float, 3> &point)
{
    const std::array<float, 3> transformed = {
        matrix[0] * point[0] + matrix[4] * point[1] + matrix[8] * point[2] + matrix[12],
        matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
        matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14],
    };
    if (!bounds.valid)
    {
        bounds.min = transformed;
        bounds.max = transformed;
        bounds.valid = true;
        return;
    }
    for (size_t axis = 0; axis < transformed.size(); ++axis)
    {
        bounds.min[axis] = std::min(bounds.min[axis], transformed[axis]);
        bounds.max[axis] = std::max(bounds.max[axis], transformed[axis]);
    }
}
}

ModelInstanceHandle ModelInstanceSystem::create(
    std::shared_ptr<const ModelAsset> asset,
    const ModelTransform &rootTransform
)
{
    if (asset == nullptr)
    {
        return {};
    }

    uint32_t index = 0;
    if (m_freeIndices.empty())
    {
        index = static_cast<uint32_t>(m_slots.size());
        m_slots.emplace_back();
    }
    else
    {
        index = m_freeIndices.back();
        m_freeIndices.pop_back();
    }

    Slot &slot = m_slots[index];
    slot.active = true;
    slot.visible = true;
    slot.outlineColorAbgr = 0;
    slot.materialVariant = 0;
    slot.nodeMarkersVisible = false;
    slot.attachments.clear();
    slot.staticStandIn.reset();
    slot.coverage = 1.0f;
    slot.playing = false;
    slot.paused = false;
    slot.clipSelected = false;
    slot.playbackMode = ModelPlaybackMode::Once;
    slot.clipIndex = 0;
    slot.timeSeconds = 0.0f;
    slot.layer = {};
    slot.transitionPose = {};
    slot.layerPose = {};
    slot.transitionElapsed = 0.0f;
    slot.transitionDuration = 0.0f;
    slot.rootTransform = rootTransform;
    slot.asset = std::move(asset);
    slot.deformationBounds.reset();
    for (const Slot &other : m_slots)
    {
        if (&other != &slot && other.active && other.asset == slot.asset)
        {
            slot.deformationBounds = other.deformationBounds;
            break;
        }
    }
    if (!slot.deformationBounds)
    {
        slot.deformationBounds = std::make_shared<ModelDeformationBounds>(buildModelDeformationBounds(*slot.asset));
    }
    evaluate(slot);
    ++m_activeCount;
    return {index, slot.generation};
}

bool ModelInstanceSystem::destroy(ModelInstanceHandle handle)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->active = false;
    pSlot->asset.reset();
    pSlot->attachments.clear();
    pSlot->staticStandIn.reset();
    pSlot->deformationBounds.reset();
    pSlot->pose = {};
    pSlot->transitionPose = {};
    pSlot->layerPose = {};
    pSlot->layer = {};
    pSlot->bounds = {};
    ++pSlot->generation;
    if (pSlot->generation == 0)
    {
        pSlot->generation = 1;
    }
    m_freeIndices.push_back(handle.index);
    --m_activeCount;
    return true;
}

void ModelInstanceSystem::clear()
{
    for (uint32_t index = 0; index < m_slots.size(); ++index)
    {
        Slot &slot = m_slots[index];
        if (!slot.active)
        {
            continue;
        }
        slot.active = false;
        slot.asset.reset();
        slot.deformationBounds.reset();
        slot.pose = {};
        slot.transitionPose = {};
        slot.layerPose = {};
        slot.layer = {};
        slot.bounds = {};
        ++slot.generation;
        if (slot.generation == 0)
        {
            slot.generation = 1;
        }
    }
    m_freeIndices.clear();
    for (uint32_t index = 0; index < m_slots.size(); ++index)
    {
        m_freeIndices.push_back(index);
    }
    m_activeCount = 0;
}

bool ModelInstanceSystem::contains(ModelInstanceHandle handle) const
{
    return find(handle) != nullptr;
}

bool ModelInstanceSystem::setTransform(ModelInstanceHandle handle, const ModelTransform &transform)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    if (pSlot->rootTransform != transform)
    {
        pSlot->rootTransform = transform;
        evaluate(*pSlot, false);
    }
    return true;
}

bool ModelInstanceSystem::setVisible(ModelInstanceHandle handle, bool visible)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->visible = visible;
    return true;
}

bool ModelInstanceSystem::setNodeMarkersVisible(ModelInstanceHandle handle, bool visible)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->nodeMarkersVisible = visible;
    return true;
}

bool ModelInstanceSystem::setMaterialVariant(ModelInstanceHandle handle, uint32_t variant)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr || variant > pSlot->asset->materialVariants.size())
    {
        return false;
    }
    pSlot->materialVariant = variant;
    return true;
}

uint32_t ModelInstanceSystem::materialVariant(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->materialVariant : 0;
}

bool ModelInstanceSystem::setOutlineColor(ModelInstanceHandle handle, uint32_t colorAbgr)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->outlineColorAbgr = colorAbgr;
    return true;
}

bool ModelInstanceSystem::setAttachments(ModelInstanceHandle handle, std::vector<ModelAttachment> attachments)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    for (const ModelAttachment &attachment : attachments)
    {
        if (attachment.asset == nullptr || attachment.nodeIndex >= pSlot->asset->nodes.size())
        {
            return false;
        }
    }
    pSlot->attachments = std::move(attachments);
    return true;
}

const std::vector<ModelAttachment> &ModelInstanceSystem::attachments(ModelInstanceHandle handle) const
{
    static const std::vector<ModelAttachment> None;
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->attachments : None;
}

bool ModelInstanceSystem::setStaticStandIn(ModelInstanceHandle handle, std::shared_ptr<const ModelAsset> asset)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->staticStandIn = std::move(asset);
    return true;
}

const std::shared_ptr<const ModelAsset> &ModelInstanceSystem::staticStandIn(ModelInstanceHandle handle) const
{
    static const std::shared_ptr<const ModelAsset> None;
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->staticStandIn : None;
}

bool ModelInstanceSystem::setCoverage(ModelInstanceHandle handle, float coverage)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->coverage = std::clamp(coverage, 0.0f, 1.0f);
    return true;
}

float ModelInstanceSystem::coverage(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->coverage : 1.0f;
}

const ModelTransform *ModelInstanceSystem::rootTransform(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? &pSlot->rootTransform : nullptr;
}

uint32_t ModelInstanceSystem::outlineColor(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->outlineColorAbgr : 0;
}

bool ModelInstanceSystem::play(ModelInstanceHandle handle, const std::string &clipName, ModelPlaybackMode mode)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    const std::optional<uint32_t> clipIndex = pSlot->asset->findClip(clipName);
    if (!clipIndex)
    {
        return false;
    }
    pSlot->clipIndex = *clipIndex;
    pSlot->layer = {};
    pSlot->transitionDuration = 0.0f;
    pSlot->clipSelected = true;
    pSlot->playbackMode = mode;
    pSlot->timeSeconds = 0.0f;
    pSlot->playing = true;
    pSlot->paused = false;
    evaluate(*pSlot);
    return true;
}

bool ModelInstanceSystem::pause(ModelInstanceHandle handle, bool paused)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->paused = paused;
    return true;
}

bool ModelInstanceSystem::stop(ModelInstanceHandle handle)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return false;
    }
    pSlot->playing = false;
    pSlot->paused = false;
    pSlot->clipSelected = false;
    pSlot->layer = {};
    pSlot->transitionDuration = 0.0f;
    pSlot->timeSeconds = 0.0f;
    evaluate(*pSlot);
    return true;
}

bool ModelInstanceSystem::setTime(ModelInstanceHandle handle, float timeSeconds)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr || !std::isfinite(timeSeconds) || timeSeconds < 0.0f)
    {
        return false;
    }
    if (!pSlot->asset->clips.empty())
    {
        const float duration = pSlot->asset->clips[pSlot->clipIndex].durationSeconds;
        pSlot->timeSeconds = std::min(timeSeconds, duration);
    }
    else
    {
        pSlot->timeSeconds = 0.0f;
    }
    evaluate(*pSlot);
    return true;
}

void ModelInstanceSystem::update(float deltaSeconds)
{
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0f)
    {
        return;
    }
    for (Slot &slot : m_slots)
    {
        if (!slot.active || !slot.playing || slot.paused || slot.asset->clips.empty())
        {
            continue;
        }
        const float duration = slot.asset->clips[slot.clipIndex].durationSeconds;
        if (duration <= 0.0f)
        {
            slot.timeSeconds = 0.0f;
            slot.playing = false;
        }
        else if (slot.playbackMode == ModelPlaybackMode::Loop)
        {
            slot.timeSeconds = std::fmod(slot.timeSeconds + deltaSeconds, duration);
        }
        else
        {
            slot.timeSeconds = std::min(slot.timeSeconds + deltaSeconds, duration);
            if (slot.timeSeconds >= duration)
            {
                slot.playing = false;
            }
        }
        evaluate(slot);
    }
}

bool ModelInstanceSystem::sample(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds,
    const ModelTransform &transform)
{
    return sampleBlended(handle, clipIndex, timeSeconds, transform, 0.0f, 0.0f);
}

bool ModelInstanceSystem::sampleBlended(ModelInstanceHandle handle, uint32_t clipIndex, float timeSeconds,
    const ModelTransform &transform, float deltaSeconds, float transitionSeconds,
    const ModelAnimationLayer &layer, bool restart)
{
    Slot *pSlot = find(handle);
    if (pSlot == nullptr || clipIndex >= pSlot->asset->clips.size() || !std::isfinite(timeSeconds) || timeSeconds < 0
        || !std::isfinite(deltaSeconds) || deltaSeconds < 0
        || !std::isfinite(transitionSeconds) || transitionSeconds < 0
        || !std::isfinite(layer.weight) || layer.weight < 0 || layer.weight > 1
        || (layer.weight > 0 && (layer.clipIndex >= pSlot->asset->clips.size()
            || !std::isfinite(layer.timeSeconds) || layer.timeSeconds < 0 || !layer.mask
            || layer.mask->size() != pSlot->asset->nodes.size()
            || std::any_of(layer.mask->begin(), layer.mask->end(), [](float weight)
                { return !std::isfinite(weight) || weight < 0.0f || weight > 1.0f; }))))
    {
        return false;
    }
    const float clampedTime = std::min(timeSeconds, pSlot->asset->clips[clipIndex].durationSeconds);
    const bool localChanged = !pSlot->clipSelected || pSlot->clipIndex != clipIndex
        || pSlot->timeSeconds != clampedTime || pSlot->layer != layer;
    const bool changed = localChanged || pSlot->rootTransform != transform;
    const bool transition = pSlot->clipSelected && (restart || pSlot->clipIndex != clipIndex
        || pSlot->layer.clipIndex != layer.clipIndex || pSlot->layer.mask != layer.mask);
    if (transitionSeconds <= 0.0f)
    {
        pSlot->transitionDuration = 0.0f;
    }
    else if (transition && pSlot->pose.matrixRevision > 0)
    {
        // Freeze the last displayed local pose, including any interrupted blend. Never evaluate hidden actors here.
        pSlot->transitionPose.localTransforms = pSlot->pose.localTransforms;
        pSlot->transitionPose.morphWeights = pSlot->pose.morphWeights;
        pSlot->transitionDuration = transitionSeconds;
        pSlot->transitionElapsed = 0.0f;
    }
    const bool blending = pSlot->transitionDuration > 0.0f;
    pSlot->transitionElapsed += deltaSeconds;
    if (pSlot->transitionElapsed >= pSlot->transitionDuration)
    {
        pSlot->transitionDuration = 0.0f;
    }
    pSlot->layer = layer;
    pSlot->clipIndex = clipIndex;
    pSlot->clipSelected = true;
    pSlot->playing = false;
    pSlot->rootTransform = transform;
    pSlot->timeSeconds = clampedTime;
    // A blend only moves while time advances: a paused world (inspect, console, dialogue) keeps its pose and palette.
    const bool blendMoved = blending && deltaSeconds > 0.0f;
    if (changed || blendMoved)
    {
        evaluate(*pSlot, localChanged || blendMoved);
    }
    return true;
}

const ModelAsset *ModelInstanceSystem::asset(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->asset.get() : nullptr;
}

std::shared_ptr<const ModelAsset> ModelInstanceSystem::sharedAsset(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->asset : nullptr;
}

const ModelPose *ModelInstanceSystem::pose(ModelInstanceHandle handle, bool deformSkins) const
{
    const Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return nullptr;
    }
    evaluateMatrices(*pSlot);
    if (!deformSkins)
    {
        if (pSlot->morphVerticesDirty)
        {
            deformModelPose(*pSlot->asset, pSlot->pose, false);
            pSlot->morphVerticesDirty = false;
        }
        return &pSlot->pose;
    }
    if (pSlot->verticesDirty)
    {
        deformModelPose(*pSlot->asset, pSlot->pose);
        pSlot->bounds = {};
        for (size_t nodeIndex = 0; nodeIndex < pSlot->asset->nodes.size(); ++nodeIndex)
        {
            const ModelNode &node = pSlot->asset->nodes[nodeIndex];
            if (node.meshIndex < 0 || !modelMatrixVisible(pSlot->pose.globalMatrices[nodeIndex]))
            {
                continue;
            }
            const ModelMesh &mesh = pSlot->asset->meshes[node.meshIndex];
            for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
            {
                const ModelPrimitive &primitive = mesh.primitives[primitiveIndex];
                const std::vector<ModelVertex> &vertices = node.skinIndex >= 0 || !primitive.morphTargets.empty()
                    ? pSlot->pose.deformedVertices[nodeIndex][primitiveIndex] : primitive.vertices;
                const ModelMatrix matrix = node.skinIndex >= 0
                    ? identityModelMatrix() : pSlot->pose.globalMatrices[nodeIndex];
                for (const ModelVertex &vertex : vertices)
                {
                    expandBounds(pSlot->bounds, matrix, vertex.position);
                }
            }
        }
        pSlot->verticesDirty = false;
        pSlot->morphVerticesDirty = false;
        pSlot->boundsDirty = false;
    }
    return &pSlot->pose;
}

const ModelMatrix *ModelInstanceSystem::nodeMatrix(ModelInstanceHandle handle, uint32_t nodeIndex) const
{
    const Slot *pSlot = find(handle);
    if (pSlot != nullptr)
    {
        evaluateMatrices(*pSlot);
    }
    if (pSlot == nullptr || nodeIndex >= pSlot->pose.globalMatrices.size())
    {
        return nullptr;
    }
    return &pSlot->pose.globalMatrices[nodeIndex];
}

const ModelMatrix *ModelInstanceSystem::nodeMatrix(ModelInstanceHandle handle, const std::string &nodeName) const
{
    const Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return nullptr;
    }
    const std::optional<uint32_t> nodeIndex = pSlot->asset->findNode(nodeName);
    return nodeIndex ? nodeMatrix(handle, *nodeIndex) : nullptr;
}

const ModelBounds *ModelInstanceSystem::bounds(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return nullptr;
    }
    evaluateMatrices(*pSlot);
    if (pSlot->boundsDirty)
    {
        pSlot->bounds = modelExactPoseBounds(*pSlot->asset, pSlot->pose);
        pSlot->boundsDirty = false;
    }
    return &pSlot->bounds;
}

const ModelBounds *ModelInstanceSystem::pickingBounds(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return nullptr;
    }
    evaluateMatrices(*pSlot);
    if (pSlot->pickingBoundsRevision != pSlot->pose.matrixRevision)
    {
        pSlot->pickingBounds = modelExactPoseBounds(*pSlot->asset, pSlot->pose, true);
        pSlot->pickingBoundsRevision = pSlot->pose.matrixRevision;
    }
    return &pSlot->pickingBounds;
}

const ModelBounds *ModelInstanceSystem::cullingBounds(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    if (pSlot == nullptr)
    {
        return nullptr;
    }
    evaluateMatrices(*pSlot);
    return &pSlot->cullingBounds;
}

const ModelBounds *ModelInstanceSystem::motionBounds(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? &pSlot->motionBounds : nullptr;
}

float ModelInstanceSystem::playbackTime(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr ? pSlot->timeSeconds : 0.0f;
}

bool ModelInstanceSystem::isPlaying(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr && pSlot->playing;
}

bool ModelInstanceSystem::isVisible(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr && pSlot->visible;
}

bool ModelInstanceSystem::areNodeMarkersVisible(ModelInstanceHandle handle) const
{
    const Slot *pSlot = find(handle);
    return pSlot != nullptr && pSlot->nodeMarkersVisible;
}

std::vector<ModelInstanceHandle> ModelInstanceSystem::handles() const
{
    std::vector<ModelInstanceHandle> result;
    result.reserve(m_activeCount);
    for (uint32_t index = 0; index < m_slots.size(); ++index)
    {
        if (m_slots[index].active)
        {
            result.push_back({index, m_slots[index].generation});
        }
    }
    return result;
}

size_t ModelInstanceSystem::size() const
{
    return m_activeCount;
}

ModelInstanceSystem::Slot *ModelInstanceSystem::find(ModelInstanceHandle handle)
{
    if (handle.index >= m_slots.size())
    {
        return nullptr;
    }
    Slot &slot = m_slots[handle.index];
    return slot.active && slot.generation == handle.generation ? &slot : nullptr;
}

const ModelInstanceSystem::Slot *ModelInstanceSystem::find(ModelInstanceHandle handle) const
{
    if (handle.index >= m_slots.size())
    {
        return nullptr;
    }
    const Slot &slot = m_slots[handle.index];
    return slot.active && slot.generation == handle.generation ? &slot : nullptr;
}

void ModelInstanceSystem::evaluate(Slot &slot, bool localPoseChanged)
{
    slot.localPoseDirty = slot.localPoseDirty || localPoseChanged;
    const float radius = slot.deformationBounds->motionRadius * std::max({std::abs(slot.rootTransform.scale[0]),
        std::abs(slot.rootTransform.scale[1]), std::abs(slot.rootTransform.scale[2])});
    slot.motionBounds = {slot.rootTransform.translation, slot.rootTransform.translation,
        slot.deformationBounds->motionRadius >= 0};
    for (size_t axis = 0; axis < 3; ++axis)
    {
        slot.motionBounds.min[axis] -= radius;
        slot.motionBounds.max[axis] += radius;
    }
    slot.matricesDirty = true;
    slot.verticesDirty = true;
    slot.morphVerticesDirty = true;
    slot.boundsDirty = true;
}

void ModelInstanceSystem::evaluateMatrices(const Slot &slot) const
{
    if (!slot.matricesDirty)
    {
        return;
    }
    if (slot.localPoseDirty && slot.clipSelected && !slot.asset->clips.empty())
    {
        evaluateModelClip(*slot.asset, slot.clipIndex, slot.timeSeconds, slot.pose);
        if (slot.layer.weight > 0.0f)
        {
            evaluateModelClip(*slot.asset, slot.layer.clipIndex, slot.layer.timeSeconds, slot.layerPose);
            blendModelPose(*slot.asset, slot.pose, slot.layerPose, slot.layer.weight, *slot.layer.mask);
        }
        if (slot.transitionDuration > 0.0f)
        {
            blendModelPose(*slot.asset, slot.pose, slot.transitionPose,
                1.0f - slot.transitionElapsed / slot.transitionDuration);
        }
    }
    else if (slot.localPoseDirty)
    {
        resetModelPose(*slot.asset, slot.pose);
    }
    slot.localPoseDirty = false;
    evaluateModelHierarchy(*slot.asset, composeModelTransform(slot.rootTransform), slot.pose);
    ++slot.pose.matrixRevision;
    // Nonnegative, normalized skin weights keep each vertex inside the union of its joint bounds.
    slot.cullingBounds = modelPoseBounds(*slot.asset, slot.pose, *slot.deformationBounds);
    slot.matricesDirty = false;
}
}
