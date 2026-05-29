#pragma once

#include "game/mm9/Mm9DatWorldRuntime.h"

#include <bgfx/bgfx.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
enum class Mm9DatWorldRenderBufferKind
{
    Static,
    Dynamic,
};

struct Mm9DatWorldRenderVertex
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float u = 0.0f;
    float v = 0.0f;

    static void init();

    static bgfx::VertexLayout ms_layout;
};

struct Mm9DatWorldRenderUploadSection
{
    size_t sectionIndex = 0;
    Mm9DatWorldRenderBufferKind bufferKind = Mm9DatWorldRenderBufferKind::Static;
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    size_t sourceModelIndex = 0;
    Mm9DatRenderPartitionBlendMode blendMode = Mm9DatRenderPartitionBlendMode::Opaque;
    size_t vertexStart = 0;
    size_t vertexCount = 0;
    size_t indexStart = 0;
    size_t indexCount = 0;
};

struct Mm9DatWorldRenderUploadPlanStats
{
    size_t sectionCount = 0;
    size_t staticSectionCount = 0;
    size_t dynamicSectionCount = 0;
    size_t staticVertexCount = 0;
    size_t staticIndexCount = 0;
    size_t dynamicVertexCount = 0;
    size_t dynamicIndexCount = 0;
    size_t invalidIndexCount = 0;
};

struct Mm9DatWorldRenderUploadPlan
{
    std::vector<Mm9DatWorldRenderVertex> staticVertices;
    std::vector<uint32_t> staticIndices;
    std::vector<Mm9DatWorldRenderVertex> dynamicVertices;
    std::vector<uint32_t> dynamicIndices;
    std::vector<Mm9DatWorldRenderUploadSection> sections;
    Mm9DatWorldRenderUploadPlanStats stats;
};

struct Mm9DatWorldGeometryResources
{
    bgfx::VertexBufferHandle staticVertexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle staticIndexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::DynamicVertexBufferHandle dynamicVertexBufferHandle = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle dynamicIndexBufferHandle = BGFX_INVALID_HANDLE;
    Mm9DatWorldRenderUploadPlanStats stats;
};

struct Mm9DatWorldTextureResource
{
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    uint32_t width = 0;
    uint32_t height = 0;
    bool loaded = false;
};

struct Mm9DatWorldTextureResources
{
    std::vector<Mm9DatWorldTextureResource> textures;
    size_t attemptedTextureCount = 0;
    size_t loadedTextureCount = 0;
    size_t failedTextureCount = 0;
};

struct Mm9DatWorldRenderSubmitCommand
{
    size_t commandIndex = 0;
    size_t sectionIndex = 0;
    Mm9DatWorldRenderBufferKind bufferKind = Mm9DatWorldRenderBufferKind::Static;
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    size_t textureResourceIndex = static_cast<size_t>(-1);
    bool hasTexture = false;
    Mm9DatRenderPartitionBlendMode blendMode = Mm9DatRenderPartitionBlendMode::Opaque;
    size_t vertexStart = 0;
    size_t vertexCount = 0;
    size_t indexStart = 0;
    size_t indexCount = 0;
    size_t triangleCount = 0;
};

struct Mm9DatWorldRenderSubmitPlanStats
{
    size_t sourceCommandCount = 0;
    size_t submittedCommandCount = 0;
    size_t skippedMissingSectionCount = 0;
    size_t skippedMissingTextureCount = 0;
    size_t staticCommandCount = 0;
    size_t dynamicCommandCount = 0;
    size_t submittedTriangleCount = 0;
    size_t submittedIndexCount = 0;
};

struct Mm9DatWorldRenderSubmitPlan
{
    std::vector<Mm9DatWorldRenderSubmitCommand> commands;
    Mm9DatWorldRenderSubmitPlanStats stats;
};

Mm9DatWorldRenderUploadPlan buildMm9DatWorldRenderUploadPlan(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld);

void applyMm9DatWorldTextureUvScale(
    Mm9DatWorldRenderUploadPlan &uploadPlan,
    const Mm9DatWorldTextureResources &textureResources);

bool refreshMm9DatWorldDynamicUploadVertices(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatWorldTextureResources &textureResources,
    Mm9DatWorldRenderUploadPlan &uploadPlan);

bool createMm9DatWorldGeometryResources(
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    Mm9DatWorldGeometryResources &resources);

bool updateMm9DatWorldDynamicGeometryResources(
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    Mm9DatWorldGeometryResources &resources);

void destroyMm9DatWorldGeometryResources(Mm9DatWorldGeometryResources &resources);

Mm9DatWorldTextureResources createMm9DatWorldTextureResources(
    const Mm9DatRuntimeTextureBindings &textureBindings);

void destroyMm9DatWorldTextureResources(Mm9DatWorldTextureResources &resources);

Mm9DatWorldRenderSubmitPlan buildMm9DatWorldRenderSubmitPlan(
    const Mm9DatRenderSubmissionPlan &runtimeSubmissionPlan,
    const Mm9DatWorldRenderUploadPlan &uploadPlan,
    const Mm9DatWorldTextureResources &textureResources);

Mm9DatWorldRenderSubmitPlanStats submitMm9DatWorldRenderSubmitPlan(
    const Mm9DatWorldRenderSubmitPlan &submitPlan,
    const Mm9DatWorldGeometryResources &geometryResources,
    const Mm9DatWorldTextureResources &textureResources,
    bgfx::ViewId viewId,
    bgfx::ProgramHandle programHandle,
    bgfx::UniformHandle textureSamplerHandle);
}
