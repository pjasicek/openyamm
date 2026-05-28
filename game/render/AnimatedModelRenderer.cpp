#include "game/render/AnimatedModelRenderer.h"

#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>

namespace OpenYAMM::Game
{
namespace
{
std::string shaderDirectoryForRenderer(bgfx::RendererType::Enum rendererType)
{
    switch (rendererType)
    {
    case bgfx::RendererType::Direct3D11:
        return "dxbc";
    case bgfx::RendererType::OpenGL:
    case bgfx::RendererType::Noop:
        return "glsl";
    case bgfx::RendererType::OpenGLES:
        return "essl";
    default:
        return {};
    }
}
}

bgfx::VertexLayout AnimatedModelSkinnedVertex::ms_layout;

void AnimatedModelSkinnedVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Indices, 4, bgfx::AttribType::Uint8)
        .add(bgfx::Attrib::Weight, 4, bgfx::AttribType::Float)
        .end();
}

void AnimatedModelRenderResources::reset()
{
    m_skinnedProgramHandle = BGFX_INVALID_HANDLE;
    m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    m_bonePaletteUniformHandle = BGFX_INVALID_HANDLE;
    m_lightParamsUniformHandle = BGFX_INVALID_HANDLE;
    m_fogColorUniformHandle = BGFX_INVALID_HANDLE;
    m_fogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
    m_fogDistancesUniformHandle = BGFX_INVALID_HANDLE;
}

void AnimatedModelRenderResources::shutdown()
{
    if (bgfx::isValid(m_skinnedProgramHandle))
    {
        bgfx::destroy(m_skinnedProgramHandle);
    }
    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
    }
    if (bgfx::isValid(m_bonePaletteUniformHandle))
    {
        bgfx::destroy(m_bonePaletteUniformHandle);
    }
    if (bgfx::isValid(m_lightParamsUniformHandle))
    {
        bgfx::destroy(m_lightParamsUniformHandle);
    }
    if (bgfx::isValid(m_fogColorUniformHandle))
    {
        bgfx::destroy(m_fogColorUniformHandle);
    }
    if (bgfx::isValid(m_fogDensitiesUniformHandle))
    {
        bgfx::destroy(m_fogDensitiesUniformHandle);
    }
    if (bgfx::isValid(m_fogDistancesUniformHandle))
    {
        bgfx::destroy(m_fogDistancesUniformHandle);
    }

    reset();
}

bool AnimatedModelRenderResources::isReady() const
{
    return bgfx::isValid(m_skinnedProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_bonePaletteUniformHandle)
        && bgfx::isValid(m_lightParamsUniformHandle)
        && bgfx::isValid(m_fogColorUniformHandle)
        && bgfx::isValid(m_fogDensitiesUniformHandle)
        && bgfx::isValid(m_fogDistancesUniformHandle);
}

bgfx::ProgramHandle AnimatedModelRenderResources::skinnedProgramHandle() const
{
    return m_skinnedProgramHandle;
}

void AnimatedModelRenderResources::setSkinnedProgramHandle(bgfx::ProgramHandle handle)
{
    m_skinnedProgramHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::textureSamplerHandle() const
{
    return m_textureSamplerHandle;
}

void AnimatedModelRenderResources::setTextureSamplerHandle(bgfx::UniformHandle handle)
{
    m_textureSamplerHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::bonePaletteUniformHandle() const
{
    return m_bonePaletteUniformHandle;
}

void AnimatedModelRenderResources::setBonePaletteUniformHandle(bgfx::UniformHandle handle)
{
    m_bonePaletteUniformHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::lightParamsUniformHandle() const
{
    return m_lightParamsUniformHandle;
}

void AnimatedModelRenderResources::setLightParamsUniformHandle(bgfx::UniformHandle handle)
{
    m_lightParamsUniformHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::fogColorUniformHandle() const
{
    return m_fogColorUniformHandle;
}

void AnimatedModelRenderResources::setFogColorUniformHandle(bgfx::UniformHandle handle)
{
    m_fogColorUniformHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::fogDensitiesUniformHandle() const
{
    return m_fogDensitiesUniformHandle;
}

void AnimatedModelRenderResources::setFogDensitiesUniformHandle(bgfx::UniformHandle handle)
{
    m_fogDensitiesUniformHandle = handle;
}

bgfx::UniformHandle AnimatedModelRenderResources::fogDistancesUniformHandle() const
{
    return m_fogDistancesUniformHandle;
}

void AnimatedModelRenderResources::setFogDistancesUniformHandle(bgfx::UniformHandle handle)
{
    m_fogDistancesUniformHandle = handle;
}

void AnimatedModelRenderer::initializeResources(AnimatedModelRenderResources &resources)
{
    AnimatedModelSkinnedVertex::init();
    resources.setSkinnedProgramHandle(loadProgram(
        "vs_animated_model_skinned.bin",
        "fs_animated_model_skinned.bin"));
    resources.setTextureSamplerHandle(bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler));
    resources.setBonePaletteUniformHandle(
        bgfx::createUniform("u_boneMatrices", bgfx::UniformType::Mat4, MaxShaderBoneMatrices));
    resources.setLightParamsUniformHandle(
        bgfx::createUniform("u_animatedModelLightParams", bgfx::UniformType::Vec4));
    resources.setFogColorUniformHandle(bgfx::createUniform("u_fogColor", bgfx::UniformType::Vec4));
    resources.setFogDensitiesUniformHandle(bgfx::createUniform("u_fogDensities", bgfx::UniformType::Vec4));
    resources.setFogDistancesUniformHandle(bgfx::createUniform("u_fogDistances", bgfx::UniformType::Vec4));
}

void AnimatedModelRenderer::shutdownResources(AnimatedModelRenderResources &resources)
{
    resources.shutdown();
}

std::vector<AnimatedModelSkinnedVertex> AnimatedModelRenderer::buildSkinnedVertices(
    const AnimatedModelDrawItem &drawItem)
{
    std::vector<AnimatedModelSkinnedVertex> vertices;
    vertices.reserve(drawItem.vertices.size());

    for (const AnimatedModelVertex &sourceVertex : drawItem.vertices)
    {
        AnimatedModelSkinnedVertex vertex = {};
        vertex.x = sourceVertex.position.x;
        vertex.y = sourceVertex.position.y;
        vertex.z = sourceVertex.position.z;
        vertex.normalX = sourceVertex.normal.x;
        vertex.normalY = sourceVertex.normal.y;
        vertex.normalZ = sourceVertex.normal.z;
        vertex.u = sourceVertex.texcoord[0];
        vertex.v = sourceVertex.texcoord[1];
        for (size_t index = 0; index < 4; ++index)
        {
            vertex.joints[index] = static_cast<uint8_t>(std::min(sourceVertex.joints[index], 255u));
            vertex.weights[index] = sourceVertex.weights[index];
        }
        vertices.push_back(vertex);
    }

    return vertices;
}

uint64_t AnimatedModelRenderer::renderStateForDrawItem(const AnimatedModelDrawItem &drawItem)
{
    uint64_t renderState =
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL;

    if (drawItem.alphaBlend)
    {
        renderState |= BGFX_STATE_BLEND_ALPHA;
    }

    if (!drawItem.doubleSided)
    {
        renderState |= BGFX_STATE_CULL_CW;
    }

    return renderState;
}

bool AnimatedModelRenderer::submitDrawItem(
    const AnimatedModelRenderResources &resources,
    uint16_t viewId,
    const AnimatedModelDrawItem &drawItem,
    const AnimatedModelMat4 &modelToWorld,
    bgfx::TextureHandle textureHandle,
    const AnimatedModelFogParameters *pFogParameters,
    const AnimatedModelLightParameters *pLightParameters)
{
    if (!resources.isReady()
        || drawItem.vertices.empty()
        || drawItem.indices.empty()
        || drawItem.bonePalette.empty()
        || drawItem.bonePalette.size() > MaxShaderBoneMatrices
        || !bgfx::isValid(textureHandle))
    {
        return false;
    }

    const std::vector<AnimatedModelSkinnedVertex> vertices = buildSkinnedVertices(drawItem);
    const uint32_t vertexCount = static_cast<uint32_t>(vertices.size());
    const uint32_t indexCount = static_cast<uint32_t>(drawItem.indices.size());

    if (bgfx::getAvailTransientVertexBuffer(vertexCount, AnimatedModelSkinnedVertex::ms_layout) < vertexCount
        || bgfx::getAvailTransientIndexBuffer(indexCount, true) < indexCount)
    {
        return false;
    }

    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::TransientIndexBuffer indexBuffer;
    bgfx::allocTransientVertexBuffer(&vertexBuffer, vertexCount, AnimatedModelSkinnedVertex::ms_layout);
    bgfx::allocTransientIndexBuffer(&indexBuffer, indexCount, true);

    std::memcpy(vertexBuffer.data, vertices.data(), vertices.size() * sizeof(AnimatedModelSkinnedVertex));
    std::memcpy(indexBuffer.data, drawItem.indices.data(), drawItem.indices.size() * sizeof(uint32_t));

    bgfx::setTransform(modelToWorld.values.data());
    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bgfx::setTexture(0, resources.textureSamplerHandle(), textureHandle);
    bgfx::setUniform(
        resources.bonePaletteUniformHandle(),
        drawItem.bonePalette.front().values.data(),
        static_cast<uint16_t>(drawItem.bonePalette.size()));
    const AnimatedModelLightParameters defaultLightParameters = {};
    const AnimatedModelLightParameters &lightParameters =
        pLightParameters != nullptr ? *pLightParameters : defaultLightParameters;
    bgfx::setUniform(resources.lightParamsUniformHandle(), lightParameters.values.data());
    const AnimatedModelFogParameters noFogParameters = {};
    const AnimatedModelFogParameters &fogParameters =
        pFogParameters != nullptr ? *pFogParameters : noFogParameters;
    bgfx::setUniform(resources.fogColorUniformHandle(), fogParameters.color.data());
    bgfx::setUniform(resources.fogDensitiesUniformHandle(), fogParameters.densities.data());
    bgfx::setUniform(resources.fogDistancesUniformHandle(), fogParameters.distances.data());
    bgfx::setState(renderStateForDrawItem(drawItem));
    bgfx::submit(viewId, resources.skinnedProgramHandle());
    return true;
}

bgfx::ShaderHandle AnimatedModelRenderer::loadShader(const char *pShaderName)
{
    const std::string shaderDirectory = shaderDirectoryForRenderer(bgfx::getRendererType());
    if (shaderDirectory.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::filesystem::path path = shaderRoot() / shaderDirectory / pShaderName;
    std::ifstream stream(path, std::ios::binary);
    if (!stream)
    {
        std::cerr << "AnimatedModelRenderer: missing shader " << path << '\n';
        return BGFX_INVALID_HANDLE;
    }

    std::vector<char> shaderBytes(
        (std::istreambuf_iterator<char>(stream)),
        std::istreambuf_iterator<char>());
    if (shaderBytes.empty())
    {
        std::cerr << "AnimatedModelRenderer: empty shader " << path << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

bgfx::ProgramHandle AnimatedModelRenderer::loadProgram(
    const char *pVertexShaderName,
    const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);
    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        if (bgfx::isValid(vertexShaderHandle))
        {
            bgfx::destroy(vertexShaderHandle);
        }
        if (bgfx::isValid(fragmentShaderHandle))
        {
            bgfx::destroy(fragmentShaderHandle);
        }
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

std::filesystem::path AnimatedModelRenderer::shaderRoot()
{
    return std::filesystem::path(OPENYAMM_BGFX_SHADER_DIR);
}
}
