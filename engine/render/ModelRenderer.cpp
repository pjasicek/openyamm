#include "engine/render/ModelRenderer.h"

#include "engine/BgfxContext.h"
#include "engine/ImageAssetLoader.h"
#include "engine/ImageMipmaps.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Engine
{
namespace
{
static_assert(sizeof(ModelVertex) == sizeof(float) * 8);

constexpr uint64_t OpaqueState = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
    BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_MSAA;
constexpr uint64_t BlendState = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL |
    BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA;
// Inspector markers intentionally ignore scene depth so empty and occluded attachment nodes remain inspectable.
constexpr uint64_t MarkerState = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_PT_LINES | BGFX_STATE_MSAA;
constexpr float MarkerAxisLength = 0.4f;

bgfx::VertexLayout modelVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
    return layout;
}

struct SkinnedVertex
{
    ModelVertex vertex;
    ModelVertexInfluences influences;
};

bgfx::VertexLayout skinnedVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Indices, 4, bgfx::AttribType::Uint16)
        .add(bgfx::Attrib::TexCoord5, 4, bgfx::AttribType::Uint16)
        .add(bgfx::Attrib::Weight, 4, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord3, 4, bgfx::AttribType::Float)
        .end();
    return layout;
}

std::array<float, 3> transformPoint(const ModelMatrix &matrix, const std::array<float, 3> &point)
{
    return {
        matrix[0] * point[0] + matrix[4] * point[1] + matrix[8] * point[2] + matrix[12],
        matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
        matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14],
    };
}

bool samplerUsesMips(const ModelSampler &sampler)
{
    return sampler.minFilter == 0 || sampler.minFilter >= 9984;
}

uint32_t samplerFlags(const ModelSampler &sampler)
{
    uint32_t flags = 0;
    if (sampler.wrapS == 33071)
    {
        flags |= BGFX_SAMPLER_U_CLAMP;
    }
    if (sampler.wrapS == 33648)
    {
        flags |= BGFX_SAMPLER_U_MIRROR;
    }
    if (sampler.wrapT == 33071)
    {
        flags |= BGFX_SAMPLER_V_CLAMP;
    }
    if (sampler.wrapT == 33648)
    {
        flags |= BGFX_SAMPLER_V_MIRROR;
    }
    if (sampler.magFilter == 9728)
    {
        flags |= BGFX_SAMPLER_MAG_POINT;
    }
    if (sampler.minFilter == 9728 || sampler.minFilter == 9984 || sampler.minFilter == 9986)
    {
        flags |= BGFX_SAMPLER_MIN_POINT;
    }
    else
    {
        flags |= BGFX_SAMPLER_MIN_ANISOTROPIC;
    }
    if (sampler.minFilter == 9984 || sampler.minFilter == 9985)
    {
        flags |= BGFX_SAMPLER_MIP_POINT;
    }
    return flags;
}

bgfx::TextureHandle createTexture(const ModelImage &image, ImageMipSemantic semantic,
    uint8_t alphaCutoff, bool mips)
{
    const std::optional<ImagePixelsBgra> decoded = decodeImagePixelsBgra(image.pngBytes, image.sourcePath);
    if (!decoded || decoded->width <= 0 || decoded->height <= 0
        || decoded->width > bgfx::getCaps()->limits.maxTextureSize
        || decoded->height > bgfx::getCaps()->limits.maxTextureSize)
    {
        throw std::runtime_error("Cannot upload model texture: " + image.sourcePath);
    }
    std::vector<BgraMipLevel> levels = prepareBgraMipChain(
        uint16_t(decoded->width), uint16_t(decoded->height), decoded->pixels, alphaCutoff, semantic);
    if (!mips)
    {
        levels.resize(1);
    }
    const uint64_t flags = semantic == ImageMipSemantic::Srgb ? BGFX_TEXTURE_SRGB : BGFX_TEXTURE_NONE;
    const bgfx::TextureHandle texture = bgfx::createTexture2D(uint16_t(decoded->width), uint16_t(decoded->height),
        mips, 1, bgfx::TextureFormat::RGBA8, flags);
    if (!bgfx::isValid(texture))
    {
        throw std::runtime_error("Cannot allocate model texture: " + image.sourcePath);
    }
    for (uint8_t index = 0; index < levels.size(); ++index)
    {
        BgraMipLevel &level = levels[index];
        for (size_t offset = 0; offset < level.pixels.size(); offset += 4)
        {
            std::swap(level.pixels[offset], level.pixels[offset + 2]);
        }
        bgfx::updateTexture2D(texture, 0, index, 0, 0, level.width, level.height,
            bgfx::copy(level.pixels.data(), uint32_t(level.pixels.size())));
    }
    return texture;
}

uint64_t cullState(const ModelMaterial &material, const ModelMatrix &matrix)
{
    if (material.doubleSided)
    {
        return 0;
    }
    return determinant3x3(matrix) < 0.0f ? BGFX_STATE_CULL_CCW : BGFX_STATE_CULL_CW;
}

}

struct ModelRenderer::Draw
{
    const PrimitiveResources *pPrimitive = nullptr;
    const AssetResources *pResources = nullptr;
    const ModelMaterial *pMaterial = nullptr;
    int materialIndex = -1;
    ModelMatrix matrix = {};
    const ModelMatrix *pCullMatrix = nullptr;
    const std::vector<ModelVertex> *pVertices = nullptr;
    uint64_t deformationRevision = 0;
    const ModelSkin *pSkin = nullptr;
    const ModelPose *pPose = nullptr;
    const ModelRenderLighting *pLighting = nullptr;
    uint32_t outlineColorAbgr = 0;
    float distanceSquared = 0.0f;
    ModelInstanceHandle instance;
};

bool ModelRenderer::bindGeometry(const Draw &draw)
{
    bgfx::setTransform(draw.matrix.data());
    bindSkin(draw);
    if (draw.pSkin != nullptr)
    {
        bgfx::setVertexBuffer(0, draw.pPrimitive->skinnedVertexBuffer);
    }
    else if (draw.pVertices != nullptr)
    {
        const uint32_t count = uint32_t(draw.pVertices->size());
        if (count == 0)
        {
            return false;
        }
        DeformedBuffer &buffer = m_deformedVertexBuffers[draw.pVertices];
        if (buffer.owner != draw.instance || buffer.count != count)
        {
            if (bgfx::isValid(buffer.handle))
            {
                bgfx::destroy(buffer.handle);
            }
            buffer = {draw.instance, bgfx::createDynamicVertexBuffer(count, modelVertexLayout()), count, 0};
        }
        if (!bgfx::isValid(buffer.handle))
        {
            throw std::runtime_error("Cannot allocate animated model vertex buffer");
        }
        if (buffer.revision != draw.deformationRevision)
        {
            bgfx::update(buffer.handle, 0, bgfx::copy(draw.pVertices->data(), count * sizeof(ModelVertex)));
            buffer.revision = draw.deformationRevision;
        }
        bgfx::setVertexBuffer(0, buffer.handle);
    }
    else
    {
        bgfx::setVertexBuffer(0, draw.pPrimitive->vertexBuffer);
    }
    bgfx::setIndexBuffer(draw.pPrimitive->indexBuffer, 0, draw.pPrimitive->indexCount);
    return true;
}

void ModelRenderer::bindSkin(const Draw &draw)
{
    float params[4] = {};
    if (draw.pSkin != nullptr)
    {
        const ModelSkin &skin = *draw.pSkin;
        const uint32_t count = uint32_t(skin.joints.size());
        SkinPalette &palette = m_skinPalettes[draw.pCullMatrix];
        if (palette.owner != draw.instance)
        {
            if (bgfx::isValid(palette.texture))
            {
                bgfx::destroy(palette.texture);
            }
            palette = {draw.instance, BGFX_INVALID_HANDLE, 0};
        }
        if (!bgfx::isValid(palette.texture))
        {
            if (count == 0 || count * 2 > bgfx::getCaps()->limits.maxTextureSize
                || !bgfx::isTextureValid(0, false, 1, bgfx::TextureFormat::RGBA32F,
                    BGFX_SAMPLER_POINT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP))
            {
                throw std::runtime_error("GPU cannot sample this model's joint palette");
            }
            palette.texture = bgfx::createTexture2D(4, uint16_t(count * 2), false, 1,
                bgfx::TextureFormat::RGBA32F, BGFX_SAMPLER_POINT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            if (!bgfx::isValid(palette.texture))
            {
                throw std::runtime_error("Cannot allocate model joint palette");
            }
        }
        if (palette.revision != draw.pPose->matrixRevision)
        {
            std::vector<ModelMatrix> matrices(count * 2);
            for (size_t index = 0; index < count; ++index)
            {
                matrices[index] = multiplyModelMatrices(
                    draw.pPose->globalMatrices[skin.joints[index]], skin.inverseBindMatrices[index]);
                matrices[count + index] = modelNormalMatrix(matrices[index]);
            }
            bgfx::updateTexture2D(palette.texture, 0, 0, 0, 0, 4, uint16_t(count * 2),
                bgfx::copy(matrices.data(), uint32_t(matrices.size() * sizeof(ModelMatrix))));
            palette.revision = draw.pPose->matrixRevision;
        }
        params[0] = 1;
        params[1] = 1.0f / (count * 2);
        params[2] = float(count);
        bgfx::setTexture(5, m_skinSamplerHandle, palette.texture);
    }
    else
    {
        bgfx::setTexture(5, m_skinSamplerHandle, m_whiteTextureHandle);
    }
    bgfx::setUniform(m_skinParamsHandle, params);
}

void ModelRenderer::submit(const Draw &draw, uint16_t viewId, const ModelRenderLighting &lighting)
{
    if (!bindGeometry(draw))
    {
        return;
    }
    const ModelMaterial &material = *draw.pMaterial;
    const float materialValues[8] = {
        material.baseColor[0], material.baseColor[1], material.baseColor[2], material.baseColor[3],
        material.alphaCutoff,
        material.alphaMode == ModelAlphaMode::Mask ? 1.0f : 0.0f,
        material.unlit ? 1.0f : 0.0f,
        material.doubleSided ? 1.0f : 0.0f,
    };
    const float lightingValues[16] = {
        lighting.lightDirection[0], lighting.lightDirection[1], lighting.lightDirection[2], lighting.direct,
        lighting.directColor[0], lighting.directColor[1], lighting.directColor[2], 0,
        lighting.ambientColor[0], lighting.ambientColor[1], lighting.ambientColor[2], lighting.ambient,
        0, 0, 0, float(std::min(lighting.pointCount, 12u)),
    };
    const ModelMatrix transformedNormals = modelNormalMatrix(draw.matrix);
    AssetResources::MaterialTextures textures;
    if (draw.materialIndex >= 0)
    {
        textures = draw.pResources->materialTextures[draw.materialIndex];
    }
    const bgfx::TextureHandle texture = bgfx::isValid(textures.base) ? textures.base : m_whiteTextureHandle;

    bgfx::setTexture(0, m_textureSamplerHandle, texture, samplerFlags(material.baseSampler));
    const bool hasNormal = bgfx::isValid(textures.normal);
    const float surface[4] = {material.emissive[0], material.emissive[1], material.emissive[2],
        hasNormal ? material.normalScale : -1.0f};
    const float pbr[4] = {material.metallic, material.roughness, 0, 0};
    bgfx::setTexture(1, m_normalSamplerHandle, hasNormal ? textures.normal : m_whiteTextureHandle,
        samplerFlags(material.normalSampler));
    bgfx::setTexture(2, m_metallicRoughnessSamplerHandle,
        bgfx::isValid(textures.metallicRoughness) ? textures.metallicRoughness : m_whiteTextureHandle,
        samplerFlags(material.metallicRoughnessSampler));
    bgfx::setUniform(m_pbrUniformHandle, pbr);
    bgfx::setUniform(m_pointPositionsUniformHandle, lighting.pointPositions.data(), 12);
    bgfx::setUniform(m_pointColorsUniformHandle, lighting.pointColors.data(), 12);
    bgfx::setUniform(m_surfaceUniformHandle, surface);
    bgfx::setUniform(m_materialUniformHandle, materialValues, 2);
    bgfx::setUniform(m_lightingUniformHandle, lightingValues, 4);
    bgfx::setUniform(m_normalMatrixUniformHandle, transformedNormals.data());
    const float environment[4] = {lighting.environmentColor[0], lighting.environmentColor[1],
        lighting.environmentColor[2], m_environmentMaxLod};
    bgfx::setUniform(m_environmentUniformHandle, environment);
    bgfx::setTexture(3, m_environmentSamplerHandle, m_environmentTextureHandle);
    bgfx::setTexture(4, m_environmentBrdfSamplerHandle, m_environmentBrdfTextureHandle);
    bindSunShadows();
    const uint64_t state = material.alphaMode == ModelAlphaMode::Blend ? BlendState : OpaqueState;
    if (draw.outlineColorAbgr != 0)
    {
        const float outline[4] = {float(draw.outlineColorAbgr & 255) / 255,
            float((draw.outlineColorAbgr >> 8) & 255) / 255, float((draw.outlineColorAbgr >> 16) & 255) / 255, 1};
        bgfx::setUniform(m_outlineUniformHandle, outline);
        bgfx::setState((OpaqueState & ~BGFX_STATE_WRITE_Z)
            | (determinant3x3(*draw.pCullMatrix) < 0 ? BGFX_STATE_CULL_CW : BGFX_STATE_CULL_CCW));
        bgfx::submit(viewId, m_programHandle, 0, BGFX_DISCARD_NONE);
    }
    const float noOutline[4] = {};
    bgfx::setUniform(m_outlineUniformHandle, noOutline);
    bgfx::setState(state | cullState(material, *draw.pCullMatrix));
    bgfx::submit(viewId, m_programHandle);
}

void ModelRenderer::submitNodeMarkers(const ModelPose &pose, uint16_t viewId) const
{
    const bgfx::VertexLayout layout = modelVertexLayout();
    for (const ModelMatrix &matrix : pose.globalMatrices)
    {
        constexpr uint32_t vertexCount = 6;
        if (bgfx::getAvailTransientVertexBuffer(vertexCount, layout) < vertexCount)
        {
            return;
        }

        bgfx::TransientVertexBuffer vertices = {};
        bgfx::allocTransientVertexBuffer(&vertices, vertexCount, layout);
        ModelVertex *pVertices = static_cast<ModelVertex *>(static_cast<void *>(vertices.data));
        for (uint32_t vertexIndex = 0; vertexIndex < vertexCount; ++vertexIndex)
        {
            pVertices[vertexIndex] = {};
        }
        pVertices[0].position = {0.0f, 0.0f, 0.0f};
        pVertices[1].position = {MarkerAxisLength, 0.0f, 0.0f};
        pVertices[2].position = {0.0f, 0.0f, 0.0f};
        pVertices[3].position = {0.0f, MarkerAxisLength, 0.0f};
        pVertices[4].position = {0.0f, 0.0f, 0.0f};
        pVertices[5].position = {0.0f, 0.0f, MarkerAxisLength};

        static constexpr std::array<std::array<float, 4>, 3> axisColors = {{
            {1.0f, 0.05f, 0.05f, 1.0f},
            {0.05f, 1.0f, 0.05f, 1.0f},
            {0.05f, 0.35f, 1.0f, 1.0f},
        }};
        const float lightingValues[16] = {};
        const ModelMatrix identity = identityModelMatrix();
        for (uint32_t axis = 0; axis < 3; ++axis)
        {
            const float materialValues[8] = {
                srgbToLinear(axisColors[axis][0]), srgbToLinear(axisColors[axis][1]),
                srgbToLinear(axisColors[axis][2]), axisColors[axis][3],
                0.5f, 0.0f, 1.0f, 0.0f,
            };
            bgfx::setTransform(matrix.data());
            bgfx::setVertexBuffer(0, &vertices, axis * 2, 2);
            bgfx::setTexture(0, m_textureSamplerHandle, m_whiteTextureHandle);
            bgfx::setUniform(m_materialUniformHandle, materialValues, 2);
            bgfx::setUniform(m_lightingUniformHandle, lightingValues, 4);
            bgfx::setUniform(m_normalMatrixUniformHandle, identity.data());
            const float surface[4] = {0, 0, 0, -1};
            bgfx::setTexture(1, m_normalSamplerHandle, m_whiteTextureHandle);
            bgfx::setTexture(2, m_metallicRoughnessSamplerHandle, m_whiteTextureHandle);
            bgfx::setTexture(3, m_environmentSamplerHandle, m_environmentTextureHandle);
            bgfx::setTexture(4, m_environmentBrdfSamplerHandle, m_environmentBrdfTextureHandle);
            bgfx::setUniform(m_surfaceUniformHandle, surface);
            bgfx::setState(MarkerState);
            const float noOutline[4] = {};
            bgfx::setUniform(m_skinParamsHandle, noOutline);
            bgfx::setTexture(5, m_skinSamplerHandle, m_whiteTextureHandle);
            bgfx::setUniform(m_outlineUniformHandle, noOutline);
            bgfx::submit(viewId, m_programHandle);
        }
    }
}

bool ModelRenderer::initialize(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle)
{
    if (!bgfx::isValid(programHandle) || !BgfxContext::isBgfxInitialized())
    {
        return false;
    }
    shutdown(true);
    m_programHandle = programHandle;
    m_shadowProgramHandle = shadowProgramHandle;
    m_shadowSamplers[0] = bgfx::createUniform("s_sunShadowNear", bgfx::UniformType::Sampler);
    m_shadowSamplers[1] = bgfx::createUniform("s_sunShadowFar", bgfx::UniformType::Sampler);
    m_shadowMatricesUniformHandle = bgfx::createUniform("u_sunShadowMatrices", bgfx::UniformType::Mat4, 2);
    m_shadowParamsUniformHandle = bgfx::createUniform("u_sunShadowParams", bgfx::UniformType::Vec4, 4);
    m_normalSamplerHandle = bgfx::createUniform("s_modelNormal", bgfx::UniformType::Sampler);
    m_skinSamplerHandle = bgfx::createUniform("s_modelJoints", bgfx::UniformType::Sampler);
    m_skinParamsHandle = bgfx::createUniform("u_modelSkin", bgfx::UniformType::Vec4);
    m_surfaceUniformHandle = bgfx::createUniform("u_modelSurface", bgfx::UniformType::Vec4);
    m_metallicRoughnessSamplerHandle = bgfx::createUniform("s_modelMetallicRoughness", bgfx::UniformType::Sampler);
    m_pbrUniformHandle = bgfx::createUniform("u_modelPbr", bgfx::UniformType::Vec4);
    m_environmentSamplerHandle = bgfx::createUniform("s_modelEnvironment", bgfx::UniformType::Sampler);
    m_environmentBrdfSamplerHandle = bgfx::createUniform("s_modelEnvironmentBrdf", bgfx::UniformType::Sampler);
    m_environmentUniformHandle = bgfx::createUniform("u_modelEnvironment", bgfx::UniformType::Vec4);
    m_pointPositionsUniformHandle = bgfx::createUniform("u_modelPointPositions", bgfx::UniformType::Vec4, 12);
    m_pointColorsUniformHandle = bgfx::createUniform("u_modelPointColors", bgfx::UniformType::Vec4, 12);
    m_fogUniformHandle = bgfx::createUniform("u_modelFog", bgfx::UniformType::Vec4, 3);
    m_cameraUniformHandle = bgfx::createUniform("u_modelCamera", bgfx::UniformType::Vec4);
    m_outlineUniformHandle = bgfx::createUniform("u_modelOutline", bgfx::UniformType::Vec4);
    m_textureSamplerHandle = bgfx::createUniform("s_modelTexture", bgfx::UniformType::Sampler);
    m_materialUniformHandle = bgfx::createUniform("u_modelMaterial", bgfx::UniformType::Vec4, 2);
    m_lightingUniformHandle = bgfx::createUniform("u_modelLighting", bgfx::UniformType::Vec4, 4);
    m_normalMatrixUniformHandle = bgfx::createUniform("u_modelNormalMatrix", bgfx::UniformType::Mat4);
    const uint32_t white = 0xffffffffu;
    m_whiteTextureHandle = bgfx::createTexture2D(
        1,
        1,
        false,
        1,
        bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
        bgfx::copy(&white, sizeof(white)));
    const bool initialized = bgfx::isValid(m_skinSamplerHandle) && bgfx::isValid(m_skinParamsHandle)
        && bgfx::isValid(m_metallicRoughnessSamplerHandle) && bgfx::isValid(m_pbrUniformHandle)
        && bgfx::isValid(m_shadowSamplers[0]) && bgfx::isValid(m_shadowSamplers[1])
        && bgfx::isValid(m_shadowMatricesUniformHandle) && bgfx::isValid(m_shadowParamsUniformHandle)
        && bgfx::isValid(m_pointPositionsUniformHandle) && bgfx::isValid(m_pointColorsUniformHandle)
        && bgfx::isValid(m_environmentSamplerHandle) && bgfx::isValid(m_environmentBrdfSamplerHandle)
        && bgfx::isValid(m_environmentUniformHandle)
        && bgfx::isValid(m_normalSamplerHandle) && bgfx::isValid(m_surfaceUniformHandle) &&
        bgfx::isValid(m_fogUniformHandle) && bgfx::isValid(m_cameraUniformHandle)
        && bgfx::isValid(m_outlineUniformHandle) &&
        bgfx::isValid(m_textureSamplerHandle) && bgfx::isValid(m_materialUniformHandle) &&
        bgfx::isValid(m_lightingUniformHandle) && bgfx::isValid(m_normalMatrixUniformHandle) &&
        bgfx::isValid(m_whiteTextureHandle);
    if (!initialized)
    {
        shutdown(true);
    }
    return initialized;
}

void ModelRenderer::shutdown(bool destroyGpu)
{
    destroySunShadows(destroyGpu);
    destroyEnvironment(destroyGpu);
    destroyDeformedBuffers(destroyGpu);
    if (destroyGpu && BgfxContext::isBgfxInitialized())
    {
        for (auto &[pAsset, resources] : m_assets)
        {
            destroy(resources);
        }
        for (const bgfx::UniformHandle handle : {m_skinSamplerHandle, m_skinParamsHandle,
                m_metallicRoughnessSamplerHandle, m_pbrUniformHandle,
                m_pointPositionsUniformHandle, m_pointColorsUniformHandle,
                m_shadowSamplers[0], m_shadowSamplers[1], m_shadowMatricesUniformHandle, m_shadowParamsUniformHandle,
                m_environmentSamplerHandle, m_environmentBrdfSamplerHandle, m_environmentUniformHandle})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
        if (bgfx::isValid(m_normalSamplerHandle))
        {
            bgfx::destroy(m_normalSamplerHandle);
        }
        if (bgfx::isValid(m_fogUniformHandle))
        {
            bgfx::destroy(m_fogUniformHandle);
        }
        if (bgfx::isValid(m_cameraUniformHandle))
        {
            bgfx::destroy(m_cameraUniformHandle);
        }
        if (bgfx::isValid(m_outlineUniformHandle))
        {
            bgfx::destroy(m_outlineUniformHandle);
        }
        if (bgfx::isValid(m_surfaceUniformHandle))
        {
            bgfx::destroy(m_surfaceUniformHandle);
        }
        if (bgfx::isValid(m_whiteTextureHandle))
        {
            bgfx::destroy(m_whiteTextureHandle);
        }
        if (bgfx::isValid(m_textureSamplerHandle))
        {
            bgfx::destroy(m_textureSamplerHandle);
        }
        if (bgfx::isValid(m_materialUniformHandle))
        {
            bgfx::destroy(m_materialUniformHandle);
        }
        if (bgfx::isValid(m_lightingUniformHandle))
        {
            bgfx::destroy(m_lightingUniformHandle);
        }
        if (bgfx::isValid(m_normalMatrixUniformHandle))
        {
            bgfx::destroy(m_normalMatrixUniformHandle);
        }
        if (bgfx::isValid(m_programHandle))
        {
            bgfx::destroy(m_programHandle);
        }
        if (bgfx::isValid(m_shadowProgramHandle))
        {
            bgfx::destroy(m_shadowProgramHandle);
        }
    }
    m_assets.clear();
    m_programHandle = BGFX_INVALID_HANDLE;
    m_shadowProgramHandle = BGFX_INVALID_HANDLE;
    m_shadowSamplers = {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    m_shadowMatricesUniformHandle = BGFX_INVALID_HANDLE;
    m_shadowParamsUniformHandle = BGFX_INVALID_HANDLE;
    m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    m_materialUniformHandle = BGFX_INVALID_HANDLE;
    m_lightingUniformHandle = BGFX_INVALID_HANDLE;
    m_normalMatrixUniformHandle = BGFX_INVALID_HANDLE;
    m_whiteTextureHandle = BGFX_INVALID_HANDLE;
    m_metallicRoughnessSamplerHandle = BGFX_INVALID_HANDLE;
    m_pbrUniformHandle = BGFX_INVALID_HANDLE;
    m_environmentSamplerHandle = BGFX_INVALID_HANDLE;
    m_environmentBrdfSamplerHandle = BGFX_INVALID_HANDLE;
    m_environmentUniformHandle = BGFX_INVALID_HANDLE;
    m_pointPositionsUniformHandle = BGFX_INVALID_HANDLE;
    m_pointColorsUniformHandle = BGFX_INVALID_HANDLE;
    m_normalSamplerHandle = BGFX_INVALID_HANDLE;
    m_skinSamplerHandle = BGFX_INVALID_HANDLE;
    m_skinParamsHandle = BGFX_INVALID_HANDLE;
    m_surfaceUniformHandle = BGFX_INVALID_HANDLE;
    m_fogUniformHandle = BGFX_INVALID_HANDLE;
    m_cameraUniformHandle = BGFX_INVALID_HANDLE;
    m_outlineUniformHandle = BGFX_INVALID_HANDLE;
}

void ModelRenderer::preload(const ModelInstanceSystem &instances)
{
    if (!bgfx::isValid(m_programHandle))
    {
        return;
    }
    pruneUnusedAssets();
    for (const ModelInstanceHandle handle : instances.handles())
    {
        prepare(instances.sharedAsset(handle));
    }
}

void ModelRenderer::beginFrame()
{
    m_shadowParams[0][0] = 0;
}

void ModelRenderer::destroyDeformedBuffers(bool destroyGpu)
{
    if (destroyGpu && BgfxContext::isBgfxInitialized())
    {
        for (const auto &[pVertices, buffer] : m_deformedVertexBuffers)
        {
            if (bgfx::isValid(buffer.handle))
            {
                bgfx::destroy(buffer.handle);
            }
        }
        for (const auto &[pMatrix, palette] : m_skinPalettes)
        {
            if (bgfx::isValid(palette.texture))
            {
                bgfx::destroy(palette.texture);
            }
        }
    }
    m_deformedVertexBuffers.clear();
    m_skinPalettes.clear();
    m_lodStates.clear();
}

void ModelRenderer::destroySunShadows(bool destroyGpu)
{
    for (size_t cascade = 0; cascade < ModelSunShadowCascades; ++cascade)
    {
        if (destroyGpu && BgfxContext::isBgfxInitialized() && bgfx::isValid(m_shadowFramebuffers[cascade]))
        {
            bgfx::destroy(m_shadowFramebuffers[cascade]);
        }
        m_shadowFramebuffers[cascade] = BGFX_INVALID_HANDLE;
        m_shadowTextures[cascade] = BGFX_INVALID_HANDLE;
    }
    m_shadowParams[0][0] = 0;
    m_shadowSize = 0;
}

void ModelRenderer::bindSunShadows() const
{
    constexpr uint32_t sampling = BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT
        | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT;
    for (size_t cascade = 0; cascade < ModelSunShadowCascades; ++cascade)
    {
        bgfx::setTexture(uint8_t(6 + cascade), m_shadowSamplers[cascade],
            bgfx::isValid(m_shadowTextures[cascade]) ? m_shadowTextures[cascade] : m_whiteTextureHandle, sampling);
    }
    bgfx::setUniform(m_shadowMatricesUniformHandle, m_shadowMatrices.data(), 2);
    bgfx::setUniform(m_shadowParamsUniformHandle, m_shadowParams.data(), 4);
}

void ModelRenderer::renderSunShadows(const ModelInstanceSystem &instances, uint16_t firstViewId,
    const std::array<float, 3> &cameraPosition, const std::array<float, 3> &lightDirection, bool enabled,
    int quality, bool lods)
{
    const ModelShadowSettings settings = modelShadowSettings(quality);
    m_shadowParams[0][0] = 0;
    const float lengthSquared = lightDirection[0] * lightDirection[0] + lightDirection[1] * lightDirection[1]
        + lightDirection[2] * lightDirection[2];
    if (!enabled || settings.size == 0 || !bgfx::isValid(m_shadowProgramHandle) || instances.size() == 0
        || !std::isfinite(lengthSquared) || lengthSquared < 0.000001f || lightDirection[2] <= 0.0f)
    {
        destroySunShadows(true);
        return;
    }
    const bgfx::Caps &caps = *bgfx::getCaps();
    if (m_shadowSize != settings.size)
    {
        destroySunShadows(true);
        m_shadowSize = settings.size;
    }
    std::array<ModelSunShadowCascade, ModelSunShadowCascades> cascades;
    for (size_t index = 0; index < cascades.size(); ++index)
    {
        cascades[index] = modelSunShadowCascade(cameraPosition, lightDirection, settings.radii[index],
            caps.homogeneousDepth, caps.originBottomLeft, settings.size);
    }
    std::array<std::vector<Draw>, ModelSunShadowCascades> cascadeDraws;
    for (size_t index = 0; index < cascades.size(); ++index)
    {
        cascadeDraws[index] = collectDraws(instances, [&](const ModelBounds &bounds)
        {
            return modelSunShadowIntersects(cascades[index], bounds);
        }, {cameraPosition, 0, settings.size / (2.0f * settings.radii[index]), int(index), lods});
        std::erase_if(cascadeDraws[index], [](const Draw &draw)
        {
            return draw.pMaterial->alphaMode == ModelAlphaMode::Blend;
        });
    }
    if (cascadeDraws[0].empty() && cascadeDraws[1].empty())
    {
        // Camera visibility does not end ownership. Receivers stay disabled until a caster returns.
        return;
    }
    constexpr uint64_t textureFlags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    for (size_t index = 0; index < cascades.size(); ++index)
    {
        if (!bgfx::isValid(m_shadowFramebuffers[index]))
        {
            const std::array<bgfx::TextureHandle, 2> textures = {
                bgfx::createTexture2D(settings.size, settings.size, false, 1,
                    bgfx::TextureFormat::RGBA8, textureFlags),
                bgfx::createTexture2D(settings.size, settings.size, false, 1,
                    bgfx::TextureFormat::D16, BGFX_TEXTURE_RT_WRITE_ONLY)};
            if (bgfx::isValid(textures[0]) && bgfx::isValid(textures[1]))
            {
                m_shadowFramebuffers[index] = bgfx::createFrameBuffer(uint8_t(textures.size()), textures.data(), true);
            }
            if (!bgfx::isValid(m_shadowFramebuffers[index]))
            {
                for (const bgfx::TextureHandle texture : textures)
                {
                    if (bgfx::isValid(texture))
                    {
                        bgfx::destroy(texture);
                    }
                }
                destroySunShadows(true);
                throw std::runtime_error("Cannot allocate creature sunlight shadow maps");
            }
            m_shadowTextures[index] = textures[0];
        }
        const uint16_t viewId = uint16_t(firstViewId + index);
        bgfx::setViewName(viewId, index == 0 ? "Creature sunlight near" : "Creature sunlight far");
        bgfx::setViewFrameBuffer(viewId, m_shadowFramebuffers[index]);
        bgfx::setViewRect(viewId, 0, 0, settings.size, settings.size);
        bgfx::setViewClear(viewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0xffffffffu, 1.0f);
        bgfx::setViewTransform(viewId, cascades[index].view.data(), cascades[index].projection.data());
        bgfx::touch(viewId);
        m_shadowMatrices[index] = cascades[index].textureMatrix;
        for (const Draw &draw : cascadeDraws[index])
        {
            const ModelBounds *pBounds = instances.cullingBounds(draw.instance);
            if (draw.pMaterial->alphaMode == ModelAlphaMode::Blend
                || !modelSunShadowIntersects(cascades[index], *pBounds) || !bindGeometry(draw))
            {
                continue;
            }
            const ModelMaterial &material = *draw.pMaterial;
            const float mask[8] = {0, 0, 0, material.baseColor[3], material.alphaCutoff,
                material.alphaMode == ModelAlphaMode::Mask ? 1.0f : 0.0f, 0, 0};
            const bgfx::TextureHandle texture = draw.materialIndex >= 0
                ? draw.pResources->materialTextures[draw.materialIndex].base : m_whiteTextureHandle;
            bgfx::setTexture(0, m_textureSamplerHandle,
                bgfx::isValid(texture) ? texture : m_whiteTextureHandle, samplerFlags(material.baseSampler));
            bgfx::setUniform(m_materialUniformHandle, mask, 2);
            bgfx::setState((OpaqueState & ~BGFX_STATE_MSAA) | cullState(material, *draw.pCullMatrix));
            bgfx::submit(viewId, m_shadowProgramHandle);
        }
    }
    if (!bgfx::isValid(m_shadowFramebuffers[0]) || !bgfx::isValid(m_shadowFramebuffers[1]))
    {
        return;
    }
    m_shadowParams = {{{1.0f, 1.0f / settings.size, 0.00003f, 0.7f},
        {cameraPosition[0], cameraPosition[1], cameraPosition[2], settings.radii.back()},
        {2.0f * settings.radii[0] / settings.size,
            2.0f * settings.radii[1] / settings.size, quality == 1 ? 1.0f : 0.0f, 0},
        {lightDirection[0] / std::sqrt(lengthSquared), lightDirection[1] / std::sqrt(lengthSquared),
            lightDirection[2] / std::sqrt(lengthSquared), 0}}};
}

std::vector<ModelRenderer::Draw> ModelRenderer::collectDraws(const ModelInstanceSystem &instances,
    const std::function<bool(const ModelBounds &)> &visibleBounds, const ModelLodView &view)
{
    std::erase_if(m_lodStates, [&](const auto &entry) { return !instances.contains(entry.second.owner); });
    pruneUnusedAssets();
    std::erase_if(m_deformedVertexBuffers, [&](const auto &entry)
    {
        if (instances.contains(entry.second.owner))
        {
            return false;
        }
        bgfx::destroy(entry.second.handle);
        return true;
    });
    std::erase_if(m_skinPalettes, [&](const auto &entry)
    {
        if (instances.contains(entry.second.owner))
        {
            return false;
        }
        bgfx::destroy(entry.second.texture);
        return true;
    });
    static const ModelMaterial defaultMaterial;
    std::vector<Draw> draws;
    for (const ModelInstanceHandle handle : instances.handles())
    {
        if (!instances.isVisible(handle))
        {
            continue;
        }
        const ModelBounds *pBounds = instances.motionBounds(handle);
        if (pBounds == nullptr || !pBounds->valid || (visibleBounds && !visibleBounds(*pBounds)))
        {
            continue;
        }
        pBounds = instances.cullingBounds(handle);
        if (pBounds == nullptr || !pBounds->valid || (visibleBounds && !visibleBounds(*pBounds)))
        {
            continue;
        }
        const std::shared_ptr<const ModelAsset> asset = instances.sharedAsset(handle);
        const ModelPose *pPose = instances.pose(handle, false);
        const AssetResources *pResources = prepare(asset);
        if (asset == nullptr || pPose == nullptr || pResources == nullptr)
        {
            continue;
        }
        const uint32_t variant = instances.materialVariant(handle);
        for (size_t nodeIndex = 0; nodeIndex < asset->nodes.size(); ++nodeIndex)
        {
            const ModelNode &node = asset->nodes[nodeIndex];
            if (node.meshIndex < 0 || static_cast<size_t>(node.meshIndex) >= pResources->meshes.size() ||
                nodeIndex >= pPose->globalMatrices.size())
            {
                continue;
            }
            const ModelMatrix &matrix = pPose->globalMatrices[nodeIndex];
            if (!modelMatrixVisible(matrix))
            {
                continue;
            }
            const ModelMesh &base = asset->meshes[node.meshIndex];
            const bool shadow = view.shadowCascade >= 0;
            LodState &state = m_lodStates[&matrix];
            if (state.owner != handle)
            {
                state = {handle};
            }
            uint32_t &level = shadow ? state.shadow[size_t(view.shadowCascade)] : state.color;
            const uint32_t count = shadow && !base.shadowMeshes.empty()
                ? uint32_t(base.shadowMeshes.size()) : uint32_t(base.lodMeshes.size() + 1);
            const float pixels = shadow ? modelBoundsDiameter(*pBounds) * view.orthographicPixelsPerUnit
                : modelProjectedPixels(*pBounds, view.camera, view.focalPixels);
            level = view.enabled && (shadow || view.focalPixels > 0)
                ? modelLodLevel(pixels, level, count, shadow) : 0;
            if (!shadow && view.forcedLevel >= 0)
            {
                level = std::min(uint32_t(view.forcedLevel), count - 1);
            }
            const uint32_t meshIndex = shadow && !base.shadowMeshes.empty() ? base.shadowMeshes[level]
                : level == 0 ? uint32_t(node.meshIndex) : base.lodMeshes[level - 1];
            const MeshResources &mesh = pResources->meshes[meshIndex];
            for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
            {
                const PrimitiveResources &primitive = mesh.primitives[primitiveIndex];
                if (!bgfx::isValid(primitive.vertexBuffer) || !bgfx::isValid(primitive.indexBuffer) ||
                    primitive.indexCount == 0)
                {
                    continue;
                }
                const ModelMaterial *pMaterial = &defaultMaterial;
                const int materialIndex = asset->meshes[meshIndex].primitives[primitiveIndex].materialIndices[variant];
                if (materialIndex >= 0 && static_cast<size_t>(materialIndex) < asset->materials.size())
                {
                    pMaterial = &asset->materials[materialIndex];
                }
                draws.push_back({
                    &primitive,
                    pResources,
                    pMaterial,
                    materialIndex,
                    node.skinIndex >= 0 ? identityModelMatrix() : matrix,
                    &matrix,
                    !asset->meshes[meshIndex].primitives[primitiveIndex].morphTargets.empty()
                        ? &pPose->deformedVertices[nodeIndex][primitiveIndex] : nullptr,
                    pPose->deformationRevision,
                    node.skinIndex >= 0 && asset->meshes[meshIndex].primitives[primitiveIndex].morphTargets.empty()
                        ? &asset->skins[node.skinIndex] : nullptr,
                    pPose,
                    nullptr,
                    instances.outlineColor(handle),
                    0,
                    handle,
                });
            }
        }
    }
    return draws;
}

void ModelRenderer::render(
    const ModelInstanceSystem &instances,
    uint16_t viewId,
    const std::array<float, 3> &cameraPosition,
    const ModelRenderLighting &lighting,
    const std::function<ModelRenderLighting(const ModelBounds &)> &lightingForBounds,
    const ModelSkyEnvironment *pSkyEnvironment,
    const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
    uint16_t transparentView)
{
    if (!bgfx::isValid(m_programHandle))
    {
        return;
    }
    if (instances.size() == 0)
    {
        pruneUnusedAssets();
        destroyDeformedBuffers(true);
        destroyEnvironment(true);
        return;
    }
    const std::array<std::array<float, 4>, 3> fog = {lighting.fogColor, lighting.fogDensities, lighting.fogDistances};
    const float camera[4] = {cameraPosition[0], cameraPosition[1], cameraPosition[2], 0};
    bgfx::setUniform(m_fogUniformHandle, fog.data(), 3);
    bgfx::setUniform(m_cameraUniformHandle, camera);
    std::unordered_map<uint32_t, ModelRenderLighting> instanceLighting;
    std::vector<Draw> opaqueDraws;
    std::vector<Draw> transparentDraws;
    // Scene consumers own the environment, even outside the camera. Loading renders prewarm it too.
    prepareEnvironment(pSkyEnvironment);
    std::vector<Draw> draws = collectDraws(instances, visibleBounds,
        {cameraPosition, focalPixels, 0, -1, true, forcedLod});
    for (Draw &draw : draws)
    {
        auto found = instanceLighting.find(draw.instance.index);
        if (found == instanceLighting.end())
        {
            const ModelBounds *pBounds = instances.cullingBounds(draw.instance);
            found = instanceLighting.emplace(draw.instance.index,
                lightingForBounds && pBounds != nullptr ? lightingForBounds(*pBounds) : lighting).first;
        }
        draw.pLighting = &found->second;
        const std::array<float, 3> center = transformPoint(*draw.pCullMatrix, draw.pPrimitive->center);
        for (size_t axis = 0; axis < 3; ++axis)
        {
            const float delta = center[axis] - cameraPosition[axis];
            draw.distanceSquared += delta * delta;
        }
        if (draw.pMaterial->alphaMode == ModelAlphaMode::Blend)
        {
            transparentDraws.push_back(draw);
        }
        else
        {
            opaqueDraws.push_back(draw);
        }
    }

    std::stable_sort(
        opaqueDraws.begin(),
        opaqueDraws.end(),
        [](const Draw &left, const Draw &right)
        {
            return left.distanceSquared < right.distanceSquared;
        });
    std::stable_sort(
        transparentDraws.begin(),
        transparentDraws.end(),
        [](const Draw &left, const Draw &right)
        {
            return left.distanceSquared > right.distanceSquared;
        });
    for (const Draw &draw : opaqueDraws)
    {
        submit(draw, viewId, *draw.pLighting);
    }
    for (const Draw &draw : transparentDraws)
    {
        submit(draw, transparentView == UINT16_MAX ? viewId : transparentView, *draw.pLighting);
    }
    for (const ModelInstanceHandle handle : instances.handles())
    {
        if (instances.isVisible(handle) && instances.areNodeMarkersVisible(handle))
        {
            const ModelBounds *pBounds = instances.cullingBounds(handle);
            if (pBounds == nullptr || (pBounds->valid && visibleBounds && !visibleBounds(*pBounds)))
            {
                continue;
            }
            if (const ModelPose *pPose = instances.pose(handle, false))
            {
                bindSunShadows();
                submitNodeMarkers(*pPose, viewId);
            }
        }
    }
}

void ModelRenderer::destroyEnvironment(bool destroyGpu)
{
    if (destroyGpu && BgfxContext::isBgfxInitialized())
    {
        for (const bgfx::TextureHandle handle : {m_environmentTextureHandle, m_environmentBrdfTextureHandle})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
    }
    m_environmentTextureHandle = BGFX_INVALID_HANDLE;
    m_environmentBrdfTextureHandle = BGFX_INVALID_HANDLE;
    m_environmentKey.clear();
    m_environmentMaxLod = 0;
}

void ModelRenderer::prepareEnvironment(const ModelSkyEnvironment *pSkyEnvironment)
{
    const std::string key = pSkyEnvironment != nullptr ? pSkyEnvironment->key : std::string();
    if (bgfx::isValid(m_environmentTextureHandle) && key == m_environmentKey)
    {
        return;
    }
    if (bgfx::isValid(m_environmentTextureHandle))
    {
        bgfx::destroy(m_environmentTextureHandle);
        m_environmentTextureHandle = BGFX_INVALID_HANDLE;
    }
    if (!bgfx::isValid(m_environmentBrdfTextureHandle))
    {
        const std::vector<uint8_t> pixels = prepareModelEnvironmentBrdf();
        m_environmentBrdfTextureHandle = bgfx::createTexture2D(ModelEnvironmentBrdfSize, ModelEnvironmentBrdfSize,
            false, 1, bgfx::TextureFormat::RGBA8, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
            bgfx::copy(pixels.data(), uint32_t(pixels.size())));
        if (!bgfx::isValid(m_environmentBrdfTextureHandle))
        {
            throw std::runtime_error("Cannot allocate model environment BRDF texture");
        }
    }
    if (pSkyEnvironment != nullptr)
    {
        const std::vector<ModelEnvironmentMip> mips = prepareModelSkyEnvironment(*pSkyEnvironment);
        m_environmentTextureHandle = bgfx::createTextureCube(mips.front().size, true, 1,
            bgfx::TextureFormat::RGBA16F, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_W_CLAMP);
        if (!bgfx::isValid(m_environmentTextureHandle))
        {
            throw std::runtime_error("Cannot allocate model sky environment texture");
        }
        for (uint8_t level = 0; level < mips.size(); ++level)
        {
            for (uint8_t face = 0; face < 6; ++face)
            {
                const ModelEnvironmentMip &mip = mips[level];
                const std::vector<uint16_t> &pixels = mip.rgbaHalfFaces[face];
                bgfx::updateTextureCube(m_environmentTextureHandle, 0, face, level, 0, 0, mip.size, mip.size,
                    bgfx::copy(pixels.data(), uint32_t(pixels.size() * sizeof(uint16_t))));
            }
        }
        m_environmentMaxLod = float(mips.size() - 1);
    }
    else
    {
        // An enclosed room uses its own subdued illumination, with no exterior image or per-room capture.
        const std::array<uint32_t, 6> white = {0xffffffffu, 0xffffffffu, 0xffffffffu,
            0xffffffffu, 0xffffffffu, 0xffffffffu};
        m_environmentTextureHandle = bgfx::createTextureCube(1, false, 1, bgfx::TextureFormat::RGBA8,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_W_CLAMP,
            bgfx::copy(white.data(), uint32_t(sizeof(white))));
        if (!bgfx::isValid(m_environmentTextureHandle))
        {
            throw std::runtime_error("Cannot allocate model room environment texture");
        }
        m_environmentMaxLod = 0;
    }
    m_environmentKey = key;
}

const ModelRenderer::AssetResources *ModelRenderer::prepare(std::shared_ptr<const ModelAsset> asset)
{
    if (asset == nullptr)
    {
        return nullptr;
    }
    const auto existing = m_assets.find(asset.get());
    if (existing != m_assets.end())
    {
        return &existing->second;
    }

    AssetResources resources;
    resources.asset = asset;
    resources.textures.reserve(asset->materials.size() * 3);
    resources.materialTextures.reserve(asset->materials.size());
    const auto textureFor = [&](int imageIndex, ImageMipSemantic semantic, uint8_t alphaCutoff,
                                const ModelSampler &sampler)
    {
        if (imageIndex < 0)
        {
            return bgfx::TextureHandle{bgfx::kInvalidHandle};
        }
        const bool mips = samplerUsesMips(sampler);
        for (const AssetResources::Texture &texture : resources.textures)
        {
            if (texture.imageIndex == imageIndex && texture.semantic == int(semantic)
                && texture.alphaCutoff == alphaCutoff && texture.mips == mips)
            {
                return texture.handle;
            }
        }
        const bgfx::TextureHandle handle = createTexture(asset->images.at(imageIndex), semantic, alphaCutoff, mips);
        resources.textures.push_back({imageIndex, int(semantic), alphaCutoff, mips, handle});
        return handle;
    };
    try
    {
        for (const ModelMaterial &material : asset->materials)
        {
            const uint8_t cutoff = material.alphaMode == ModelAlphaMode::Mask
                ? uint8_t(std::clamp(std::ceil(material.alphaCutoff * 255 / std::max(material.baseColor[3], 1.0e-6f)),
                    1.0f, 255.0f)) : 0;
            resources.materialTextures.push_back({
                textureFor(material.imageIndex, ImageMipSemantic::Srgb, cutoff, material.baseSampler),
                textureFor(material.normalImageIndex, ImageMipSemantic::Normal, 0, material.normalSampler),
                textureFor(material.metallicRoughnessImageIndex, ImageMipSemantic::Linear, 0,
                    material.metallicRoughnessSampler),
            });
        }
    }
    catch (...)
    {
        destroy(resources);
        throw;
    }
    const bgfx::VertexLayout layout = modelVertexLayout();
    resources.meshes.reserve(asset->meshes.size());
    for (const ModelMesh &mesh : asset->meshes)
    {
        MeshResources meshResources;
        meshResources.primitives.reserve(mesh.primitives.size());
        for (const ModelPrimitive &primitive : mesh.primitives)
        {
            PrimitiveResources primitiveResources;
            primitiveResources.indexCount = static_cast<uint32_t>(primitive.indices.size());
            if (!primitive.vertices.empty() && !primitive.indices.empty())
            {
                primitiveResources.vertexBuffer = bgfx::createVertexBuffer(
                    bgfx::copy(
                        primitive.vertices.data(),
                        static_cast<uint32_t>(primitive.vertices.size() * sizeof(ModelVertex))),
                    layout);
                if (!primitive.influences.empty() && primitive.morphTargets.empty())
                {
                    std::vector<SkinnedVertex> vertices(primitive.vertices.size());
                    for (size_t index = 0; index < vertices.size(); ++index)
                    {
                        vertices[index] = {primitive.vertices[index], primitive.influences[index]};
                    }
                    primitiveResources.skinnedVertexBuffer = bgfx::createVertexBuffer(
                        bgfx::copy(vertices.data(), uint32_t(vertices.size() * sizeof(SkinnedVertex))),
                        skinnedVertexLayout());
                    if (!bgfx::isValid(primitiveResources.skinnedVertexBuffer))
                    {
                        throw std::runtime_error("Cannot allocate model skin vertex buffer");
                    }
                }
                primitiveResources.indexBuffer = bgfx::createIndexBuffer(
                    bgfx::copy(
                        primitive.indices.data(),
                        static_cast<uint32_t>(primitive.indices.size() * sizeof(uint32_t))),
                    BGFX_BUFFER_INDEX32);
                std::array<float, 3> min = primitive.vertices.front().position;
                std::array<float, 3> max = min;
                for (const ModelVertex &vertex : primitive.vertices)
                {
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        min[axis] = std::min(min[axis], vertex.position[axis]);
                        max[axis] = std::max(max[axis], vertex.position[axis]);
                    }
                }
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    primitiveResources.center[axis] = (min[axis] + max[axis]) * 0.5f;
                }
            }
            meshResources.primitives.push_back(primitiveResources);
        }
        resources.meshes.push_back(std::move(meshResources));
    }
    return &m_assets.emplace(asset.get(), std::move(resources)).first->second;
}

void ModelRenderer::pruneUnusedAssets()
{
    for (auto entry = m_assets.begin(); entry != m_assets.end();)
    {
        if (entry->second.asset.use_count() == 1)
        {
            destroy(entry->second);
            entry = m_assets.erase(entry);
        }
        else
        {
            ++entry;
        }
    }
}

void ModelRenderer::destroy(AssetResources &resources)
{
    for (const AssetResources::Texture &texture : resources.textures)
    {
        if (bgfx::isValid(texture.handle))
        {
            bgfx::destroy(texture.handle);
        }
    }
    for (MeshResources &mesh : resources.meshes)
    {
        for (PrimitiveResources &primitive : mesh.primitives)
        {
            if (bgfx::isValid(primitive.skinnedVertexBuffer))
            {
                bgfx::destroy(primitive.skinnedVertexBuffer);
            }
            if (bgfx::isValid(primitive.vertexBuffer))
            {
                bgfx::destroy(primitive.vertexBuffer);
            }
            if (bgfx::isValid(primitive.indexBuffer))
            {
                bgfx::destroy(primitive.indexBuffer);
            }
        }
    }
}
}
