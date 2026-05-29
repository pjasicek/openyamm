#include "game/mm9/Mm9DatWorldRenderer.h"

#include "game/mm9/Mm9DtxTexture.h"

#include <algorithm>
#include <cstring>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
Mm9DatWorldRenderVertex renderVertex(const Mm9DatPreparedRenderVertex &sourceVertex)
{
    Mm9DatWorldRenderVertex vertex = {};
    vertex.x = sourceVertex.x;
    vertex.y = sourceVertex.z;
    vertex.z = sourceVertex.y;
    vertex.u = sourceVertex.uPixels;
    vertex.v = sourceVertex.vPixels;
    return vertex;
}

void destroyTextureHandle(bgfx::TextureHandle &handle)
{
    if (bgfx::isValid(handle))
    {
        bgfx::destroy(handle);
        handle = BGFX_INVALID_HANDLE;
    }
}

template <typename HandleType>
void destroyBufferHandle(HandleType &handle)
{
    if (bgfx::isValid(handle))
    {
        bgfx::destroy(handle);
        handle = BGFX_INVALID_HANDLE;
    }
}

bool createStaticVertexBuffer(
    const std::vector<Mm9DatWorldRenderVertex> &vertices,
    bgfx::VertexBufferHandle &handle)
{
    if (vertices.empty())
    {
        return true;
    }

    handle = bgfx::createVertexBuffer(
        bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(Mm9DatWorldRenderVertex))),
        Mm9DatWorldRenderVertex::ms_layout);
    return bgfx::isValid(handle);
}

bool createIndexBuffer(const std::vector<uint32_t> &indices, bgfx::IndexBufferHandle &handle)
{
    if (indices.empty())
    {
        return true;
    }

    handle = bgfx::createIndexBuffer(
        bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint32_t))),
        BGFX_BUFFER_INDEX32);
    return bgfx::isValid(handle);
}

bool createDynamicVertexBuffer(
    const std::vector<Mm9DatWorldRenderVertex> &vertices,
    bgfx::DynamicVertexBufferHandle &handle)
{
    if (vertices.empty())
    {
        return true;
    }

    handle = bgfx::createDynamicVertexBuffer(
        static_cast<uint32_t>(vertices.size()),
        Mm9DatWorldRenderVertex::ms_layout,
        BGFX_BUFFER_NONE);
    if (!bgfx::isValid(handle))
    {
        return false;
    }

    bgfx::update(
        handle,
        0,
        bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(Mm9DatWorldRenderVertex))));
    return true;
}

bgfx::TextureHandle createTextureHandle(const Mm9DtxTexture &texture)
{
    if (texture.width == 0 || texture.height == 0 || texture.pixelsBgra.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createTexture2D(
        static_cast<uint16_t>(std::min<uint32_t>(texture.width, UINT16_MAX)),
        static_cast<uint16_t>(std::min<uint32_t>(texture.height, UINT16_MAX)),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
        bgfx::copy(texture.pixelsBgra.data(), static_cast<uint32_t>(texture.pixelsBgra.size())));
}

uint64_t bgfxStateForBlendMode(Mm9DatRenderPartitionBlendMode blendMode)
{
    uint64_t state = BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LESS;

    if (blendMode == Mm9DatRenderPartitionBlendMode::Opaque)
    {
        state |= BGFX_STATE_WRITE_Z;
    }
    else
    {
        state |= BGFX_STATE_BLEND_ALPHA;
    }

    return state;
}

bool commandRangeFits(
    const Mm9DatWorldRenderSubmitCommand &command,
    const Mm9DatWorldRenderUploadPlanStats &stats)
{
    const bool dynamic = command.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic;
    const size_t vertexCount = dynamic ? stats.dynamicVertexCount : stats.staticVertexCount;
    const size_t indexCount = dynamic ? stats.dynamicIndexCount : stats.staticIndexCount;

    return command.vertexStart <= vertexCount
        && command.vertexCount <= vertexCount - command.vertexStart
        && command.indexStart <= indexCount
        && command.indexCount <= indexCount - command.indexStart;
}

const Mm9DatWorldTextureResource *textureForMaterialIndex(
    const Mm9DatWorldTextureResources &textureResources,
    size_t materialIndex)
{
    for (const Mm9DatWorldTextureResource &texture : textureResources.textures)
    {
        if (texture.materialIndex == materialIndex && texture.loaded && texture.width != 0 && texture.height != 0)
        {
            return &texture;
        }
    }

    return nullptr;
}

void scaleSectionUvs(
    const Mm9DatWorldTextureResources &textureResources,
    const Mm9DatWorldRenderUploadSection &section,
    std::vector<Mm9DatWorldRenderVertex> &vertices)
{
    const Mm9DatWorldTextureResource *pTexture = textureForMaterialIndex(textureResources, section.materialIndex);

    if (pTexture == nullptr || section.vertexStart >= vertices.size())
    {
        return;
    }

    const size_t vertexEnd = std::min(vertices.size(), section.vertexStart + section.vertexCount);
    const float uScale = 1.0f / static_cast<float>(pTexture->width);
    const float vScale = 1.0f / static_cast<float>(pTexture->height);

    for (size_t vertexIndex = section.vertexStart; vertexIndex < vertexEnd; ++vertexIndex)
    {
        vertices[vertexIndex].u *= uScale;
        vertices[vertexIndex].v *= vScale;
    }
}
}

bgfx::VertexLayout Mm9DatWorldRenderVertex::ms_layout;

void Mm9DatWorldRenderVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

Mm9DatWorldRenderUploadPlan buildMm9DatWorldRenderUploadPlan(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld)
{
    Mm9DatWorldRenderUploadPlan plan = {};
    plan.sections.reserve(preparedRenderWorld.sections.size());

    for (const Mm9DatPreparedRenderSection &sourceSection : preparedRenderWorld.sections)
    {
        if (sourceSection.vertexCount == 0 || sourceSection.indexCount == 0)
        {
            continue;
        }

        Mm9DatWorldRenderUploadSection section = {};
        section.sectionIndex = sourceSection.sectionIndex;
        section.bufferKind =
            sourceSection.dynamic ? Mm9DatWorldRenderBufferKind::Dynamic : Mm9DatWorldRenderBufferKind::Static;
        section.materialIndex = sourceSection.materialIndex;
        section.sourceModelIndex = sourceSection.sourceModelIndex;
        section.blendMode = sourceSection.blendMode;

        std::vector<Mm9DatWorldRenderVertex> &targetVertices =
            sourceSection.dynamic ? plan.dynamicVertices : plan.staticVertices;
        std::vector<uint32_t> &targetIndices =
            sourceSection.dynamic ? plan.dynamicIndices : plan.staticIndices;

        section.vertexStart = targetVertices.size();
        section.indexStart = targetIndices.size();

        for (size_t vertexOffset = 0; vertexOffset < sourceSection.vertexCount; ++vertexOffset)
        {
            const size_t sourceVertexIndex = sourceSection.vertexStart + vertexOffset;
            if (sourceVertexIndex >= preparedRenderWorld.vertices.size())
            {
                break;
            }

            targetVertices.push_back(renderVertex(preparedRenderWorld.vertices[sourceVertexIndex]));
        }

        section.vertexCount = targetVertices.size() - section.vertexStart;

        for (size_t indexOffset = 0; indexOffset < sourceSection.indexCount; ++indexOffset)
        {
            const size_t sourceIndexIndex = sourceSection.indexStart + indexOffset;
            if (sourceIndexIndex >= preparedRenderWorld.indices.size())
            {
                ++plan.stats.invalidIndexCount;
                continue;
            }

            const uint32_t sourceVertexIndex = preparedRenderWorld.indices[sourceIndexIndex];
            if (sourceVertexIndex < sourceSection.vertexStart
                || sourceVertexIndex >= sourceSection.vertexStart + section.vertexCount)
            {
                ++plan.stats.invalidIndexCount;
                continue;
            }

            const uint32_t localVertexIndex = sourceVertexIndex - static_cast<uint32_t>(sourceSection.vertexStart);
            targetIndices.push_back(static_cast<uint32_t>(section.vertexStart) + localVertexIndex);
        }

        section.indexCount = targetIndices.size() - section.indexStart;
        plan.sections.push_back(section);
    }

    plan.stats.sectionCount = plan.sections.size();
    plan.stats.staticVertexCount = plan.staticVertices.size();
    plan.stats.staticIndexCount = plan.staticIndices.size();
    plan.stats.dynamicVertexCount = plan.dynamicVertices.size();
    plan.stats.dynamicIndexCount = plan.dynamicIndices.size();

    for (const Mm9DatWorldRenderUploadSection &section : plan.sections)
    {
        if (section.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic)
        {
            ++plan.stats.dynamicSectionCount;
        }
        else
        {
            ++plan.stats.staticSectionCount;
        }
    }

    return plan;
}

void applyMm9DatWorldTextureUvScale(
    Mm9DatWorldRenderUploadPlan &uploadPlan,
    const Mm9DatWorldTextureResources &textureResources)
{
    for (const Mm9DatWorldRenderUploadSection &section : uploadPlan.sections)
    {
        if (section.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic)
        {
            scaleSectionUvs(textureResources, section, uploadPlan.dynamicVertices);
        }
        else
        {
            scaleSectionUvs(textureResources, section, uploadPlan.staticVertices);
        }
    }
}

bool refreshMm9DatWorldDynamicUploadVertices(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatWorldTextureResources &textureResources,
    Mm9DatWorldRenderUploadPlan &uploadPlan)
{
    std::unordered_map<size_t, size_t> uploadSectionIndexByRuntimeSectionIndex;
    uploadSectionIndexByRuntimeSectionIndex.reserve(uploadPlan.sections.size());

    for (size_t uploadSectionIndex = 0; uploadSectionIndex < uploadPlan.sections.size(); ++uploadSectionIndex)
    {
        const Mm9DatWorldRenderUploadSection &section = uploadPlan.sections[uploadSectionIndex];
        if (section.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic)
        {
            uploadSectionIndexByRuntimeSectionIndex.emplace(section.sectionIndex, uploadSectionIndex);
        }
    }

    for (const Mm9DatPreparedRenderSection &sourceSection : preparedRenderWorld.sections)
    {
        if (!sourceSection.dynamic)
        {
            continue;
        }

        const std::unordered_map<size_t, size_t>::const_iterator uploadIt =
            uploadSectionIndexByRuntimeSectionIndex.find(sourceSection.sectionIndex);
        if (uploadIt == uploadSectionIndexByRuntimeSectionIndex.end())
        {
            continue;
        }

        Mm9DatWorldRenderUploadSection &targetSection = uploadPlan.sections[uploadIt->second];
        if (targetSection.vertexStart > uploadPlan.dynamicVertices.size()
            || targetSection.vertexCount > uploadPlan.dynamicVertices.size() - targetSection.vertexStart)
        {
            return false;
        }

        if (targetSection.vertexCount != sourceSection.vertexCount)
        {
            return false;
        }

        for (size_t vertexOffset = 0; vertexOffset < sourceSection.vertexCount; ++vertexOffset)
        {
            const size_t sourceVertexIndex = sourceSection.vertexStart + vertexOffset;
            if (sourceVertexIndex >= preparedRenderWorld.vertices.size())
            {
                return false;
            }

            uploadPlan.dynamicVertices[targetSection.vertexStart + vertexOffset] =
                renderVertex(preparedRenderWorld.vertices[sourceVertexIndex]);
        }

        scaleSectionUvs(textureResources, targetSection, uploadPlan.dynamicVertices);
    }

    return true;
}

bool createMm9DatWorldGeometryResources(
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    Mm9DatWorldGeometryResources &resources)
{
    destroyMm9DatWorldGeometryResources(resources);
    Mm9DatWorldRenderVertex::init();

    resources.stats = uploadPlan.stats;
    if (!createStaticVertexBuffer(uploadPlan.staticVertices, resources.staticVertexBufferHandle)
        || !createIndexBuffer(uploadPlan.staticIndices, resources.staticIndexBufferHandle)
        || !createDynamicVertexBuffer(uploadPlan.dynamicVertices, resources.dynamicVertexBufferHandle)
        || !createIndexBuffer(uploadPlan.dynamicIndices, resources.dynamicIndexBufferHandle))
    {
        destroyMm9DatWorldGeometryResources(resources);
        return false;
    }

    return true;
}

bool updateMm9DatWorldDynamicGeometryResources(
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    Mm9DatWorldGeometryResources &resources)
{
    if (uploadPlan.dynamicVertices.empty())
    {
        return true;
    }

    if (!bgfx::isValid(resources.dynamicVertexBufferHandle)
        || resources.stats.dynamicVertexCount != uploadPlan.dynamicVertices.size())
    {
        return false;
    }

    bgfx::update(
        resources.dynamicVertexBufferHandle,
        0,
        bgfx::copy(
            uploadPlan.dynamicVertices.data(),
            static_cast<uint32_t>(uploadPlan.dynamicVertices.size() * sizeof(Mm9DatWorldRenderVertex))));
    return true;
}

void destroyMm9DatWorldGeometryResources(Mm9DatWorldGeometryResources &resources)
{
    destroyBufferHandle(resources.staticVertexBufferHandle);
    destroyBufferHandle(resources.staticIndexBufferHandle);
    destroyBufferHandle(resources.dynamicVertexBufferHandle);
    destroyBufferHandle(resources.dynamicIndexBufferHandle);
    resources.stats = {};
}

Mm9DatWorldTextureResources createMm9DatWorldTextureResources(
    const Mm9DatRuntimeTextureBindings &textureBindings)
{
    Mm9DatWorldTextureResources resources = {};
    resources.textures.reserve(textureBindings.bindings.size());

    for (const Mm9DatRuntimeTextureBinding &binding : textureBindings.bindings)
    {
        if (!binding.resolved || binding.physicalPath.empty())
        {
            continue;
        }

        ++resources.attemptedTextureCount;
        Mm9DatWorldTextureResource textureResource = {};
        textureResource.materialIndex = binding.materialIndex;

        std::string errorMessage;
        const std::optional<Mm9DtxTexture> texture = loadMm9DtxTexture(binding.physicalPath, errorMessage);
        if (texture.has_value())
        {
            textureResource.textureHandle = createTextureHandle(*texture);
            textureResource.width = texture->width;
            textureResource.height = texture->height;
            textureResource.loaded = bgfx::isValid(textureResource.textureHandle);
        }

        if (textureResource.loaded)
        {
            ++resources.loadedTextureCount;
        }
        else
        {
            ++resources.failedTextureCount;
        }

        resources.textures.push_back(textureResource);
    }

    return resources;
}

void destroyMm9DatWorldTextureResources(Mm9DatWorldTextureResources &resources)
{
    for (Mm9DatWorldTextureResource &texture : resources.textures)
    {
        destroyTextureHandle(texture.textureHandle);
        texture.loaded = false;
    }

    resources = {};
}

Mm9DatWorldRenderSubmitPlan buildMm9DatWorldRenderSubmitPlan(
    const Mm9DatRenderSubmissionPlan &runtimeSubmissionPlan,
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    const Mm9DatWorldTextureResources &textureResources)
{
    Mm9DatWorldRenderSubmitPlan plan = {};
    plan.stats.sourceCommandCount = runtimeSubmissionPlan.commands.size();
    plan.commands.reserve(runtimeSubmissionPlan.commands.size());

    std::unordered_map<size_t, size_t> uploadSectionIndexByRuntimeSectionIndex;
    uploadSectionIndexByRuntimeSectionIndex.reserve(uploadPlan.sections.size());
    for (size_t uploadSectionIndex = 0; uploadSectionIndex < uploadPlan.sections.size(); ++uploadSectionIndex)
    {
        uploadSectionIndexByRuntimeSectionIndex.emplace(
            uploadPlan.sections[uploadSectionIndex].sectionIndex,
            uploadSectionIndex);
    }

    std::unordered_map<size_t, size_t> textureResourceIndexByMaterialIndex;
    textureResourceIndexByMaterialIndex.reserve(textureResources.textures.size());
    for (size_t textureResourceIndex = 0;
         textureResourceIndex < textureResources.textures.size();
         ++textureResourceIndex)
    {
        const Mm9DatWorldTextureResource &texture = textureResources.textures[textureResourceIndex];
        if (!texture.loaded || !bgfx::isValid(texture.textureHandle))
        {
            continue;
        }

        textureResourceIndexByMaterialIndex.emplace(texture.materialIndex, textureResourceIndex);
    }

    for (const Mm9DatRenderDrawCommand &runtimeCommand : runtimeSubmissionPlan.commands)
    {
        const std::unordered_map<size_t, size_t>::const_iterator uploadSectionIt =
            uploadSectionIndexByRuntimeSectionIndex.find(runtimeCommand.sectionIndex);
        if (uploadSectionIt == uploadSectionIndexByRuntimeSectionIndex.end())
        {
            ++plan.stats.skippedMissingSectionCount;
            continue;
        }

        const Mm9DatWorldRenderUploadSection &uploadSection = uploadPlan.sections[uploadSectionIt->second];
        const std::unordered_map<size_t, size_t>::const_iterator textureIt =
            textureResourceIndexByMaterialIndex.find(uploadSection.materialIndex);
        if (textureIt == textureResourceIndexByMaterialIndex.end())
        {
            ++plan.stats.skippedMissingTextureCount;
            continue;
        }

        Mm9DatWorldRenderSubmitCommand command = {};
        command.sectionIndex = uploadSection.sectionIndex;
        command.bufferKind = uploadSection.bufferKind;
        command.materialIndex = uploadSection.materialIndex;
        command.textureResourceIndex = textureIt->second;
        command.hasTexture = true;
        command.blendMode = uploadSection.blendMode;
        command.vertexStart = uploadSection.vertexStart;
        command.vertexCount = uploadSection.vertexCount;
        command.indexStart = uploadSection.indexStart;
        command.indexCount = uploadSection.indexCount;
        command.triangleCount = uploadSection.indexCount / 3;
        plan.commands.push_back(command);
    }

    for (size_t commandIndex = 0; commandIndex < plan.commands.size(); ++commandIndex)
    {
        Mm9DatWorldRenderSubmitCommand &command = plan.commands[commandIndex];
        command.commandIndex = commandIndex;
        ++plan.stats.submittedCommandCount;
        plan.stats.submittedTriangleCount += command.triangleCount;
        plan.stats.submittedIndexCount += command.indexCount;

        if (command.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic)
        {
            ++plan.stats.dynamicCommandCount;
        }
        else
        {
            ++plan.stats.staticCommandCount;
        }
    }

    return plan;
}

Mm9DatWorldRenderSubmitPlanStats submitMm9DatWorldRenderSubmitPlan(
    const Mm9DatWorldRenderSubmitPlan &submitPlan,
    const Mm9DatWorldGeometryResources &geometryResources,
    const Mm9DatWorldTextureResources &textureResources,
    bgfx::ViewId viewId,
    bgfx::ProgramHandle programHandle,
    bgfx::UniformHandle textureSamplerHandle)
{
    Mm9DatWorldRenderSubmitPlanStats stats = {};
    stats.sourceCommandCount = submitPlan.commands.size();

    if (!bgfx::isValid(programHandle) || !bgfx::isValid(textureSamplerHandle))
    {
        return stats;
    }

    for (const Mm9DatWorldRenderSubmitCommand &command : submitPlan.commands)
    {
        if (!commandRangeFits(command, geometryResources.stats))
        {
            ++stats.skippedMissingSectionCount;
            continue;
        }

        if (command.textureResourceIndex >= textureResources.textures.size())
        {
            ++stats.skippedMissingTextureCount;
            continue;
        }

        const Mm9DatWorldTextureResource &texture = textureResources.textures[command.textureResourceIndex];
        if (!texture.loaded || !bgfx::isValid(texture.textureHandle))
        {
            ++stats.skippedMissingTextureCount;
            continue;
        }

        if (command.bufferKind == Mm9DatWorldRenderBufferKind::Dynamic)
        {
            if (!bgfx::isValid(geometryResources.dynamicVertexBufferHandle)
                || !bgfx::isValid(geometryResources.dynamicIndexBufferHandle))
            {
                ++stats.skippedMissingSectionCount;
                continue;
            }

            bgfx::setVertexBuffer(
                0,
                geometryResources.dynamicVertexBufferHandle,
                static_cast<uint32_t>(command.vertexStart),
                static_cast<uint32_t>(command.vertexCount));
            bgfx::setIndexBuffer(
                geometryResources.dynamicIndexBufferHandle,
                static_cast<uint32_t>(command.indexStart),
                static_cast<uint32_t>(command.indexCount));
            ++stats.dynamicCommandCount;
        }
        else
        {
            if (!bgfx::isValid(geometryResources.staticVertexBufferHandle)
                || !bgfx::isValid(geometryResources.staticIndexBufferHandle))
            {
                ++stats.skippedMissingSectionCount;
                continue;
            }

            bgfx::setVertexBuffer(
                0,
                geometryResources.staticVertexBufferHandle,
                static_cast<uint32_t>(command.vertexStart),
                static_cast<uint32_t>(command.vertexCount));
            bgfx::setIndexBuffer(
                geometryResources.staticIndexBufferHandle,
                static_cast<uint32_t>(command.indexStart),
                static_cast<uint32_t>(command.indexCount));
            ++stats.staticCommandCount;
        }

        bgfx::setTexture(0, textureSamplerHandle, texture.textureHandle);
        bgfx::setState(bgfxStateForBlendMode(command.blendMode));
        bgfx::submit(viewId, programHandle);

        ++stats.submittedCommandCount;
        stats.submittedTriangleCount += command.triangleCount;
        stats.submittedIndexCount += command.indexCount;
    }

    return stats;
}
}
