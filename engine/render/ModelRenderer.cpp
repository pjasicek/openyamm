#include "engine/render/ModelRenderer.h"

#include "engine/BgfxContext.h"
#include "engine/ImageAssetLoader.h"
#include "engine/ImageMipmaps.h"
#include "engine/render/CookedTexture.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <tuple>
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

// Unskinned vertex buffers carry the glTF vertex colour (white when absent) for static placements.
struct ColoredVertex
{
    ModelVertex vertex;
    std::array<uint8_t, 4> color;
};

bgfx::VertexLayout coloredVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
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

// A cooked texture is uploaded as it was prepared offline. It must match how the material samples it, and the GPU
// must support its codec (each platform's package carries its own texture profile); there is no RGBA fallback.
bgfx::TextureHandle createCookedTexture(const ModelImage &image, ImageMipSemantic semantic,
    uint8_t alphaCutoff, bool mips)
{
    CookedTexture cooked;
    try
    {
        cooked = decodeCookedTexture(image.bytes);
    }
    catch (const std::exception &exception)
    {
        throw std::runtime_error("Cannot upload model texture " + image.sourcePath + ": " + exception.what());
    }
    if (cooked.semantic != semantic || cooked.alphaCutoff != alphaCutoff || (cooked.levels > 1) != mips)
    {
        throw std::runtime_error("Cooked model texture " + image.sourcePath
            + " was prepared for another use (semantic, alpha cutoff or mips); re-cook the model");
    }
    const bgfx::TextureFormat::Enum format = textureBlockFormat(cooked.codec);
    const bool srgb = semantic == ImageMipSemantic::Srgb;
    const uint16_t required = srgb ? BGFX_CAPS_FORMAT_TEXTURE_2D_SRGB : BGFX_CAPS_FORMAT_TEXTURE_2D;
    if ((bgfx::getCaps()->formats[format] & required) == 0)
    {
        throw std::runtime_error("The GPU cannot sample " + std::string(textureBlockCodecName(cooked.codec))
            + (srgb ? " (sRGB)" : "") + " textures, used by " + image.sourcePath
            + "; install the asset package built for this platform's texture profile");
    }
    if (cooked.width > bgfx::getCaps()->limits.maxTextureSize || cooked.height > bgfx::getCaps()->limits.maxTextureSize)
    {
        throw std::runtime_error("Cooked model texture exceeds the GPU size limit: " + image.sourcePath);
    }
    const bgfx::TextureHandle texture = bgfx::createTexture2D(cooked.width, cooked.height, cooked.levels > 1, 1,
        format, srgb ? BGFX_TEXTURE_SRGB : BGFX_TEXTURE_NONE,
        bgfx::copy(cooked.blocks.data(), uint32_t(cooked.blocks.size())));
    if (!bgfx::isValid(texture))
    {
        throw std::runtime_error("Cannot allocate model texture: " + image.sourcePath);
    }
    return texture;
}

bgfx::TextureHandle createTexture(const ModelImage &image, ImageMipSemantic semantic,
    uint8_t alphaCutoff, bool mips)
{
    if (image.cooked)
    {
        return createCookedTexture(image, semantic, alphaCutoff, mips);
    }
    const std::optional<ImagePixelsBgra> decoded = decodeImagePixelsBgra(image.bytes, image.sourcePath);
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

// One row per colour region (mask channel order), 16 stops, sRGB-encoded so the sampler decodes and interpolates.
bgfx::TextureHandle createRampTexture(const ModelMaterial &material)
{
    if (material.regionRamps.empty())
    {
        return BGFX_INVALID_HANDLE;
    }
    std::vector<uint8_t> pixels(ModelColorRampStops * ModelMaxColorRegions * 4, 255);
    for (size_t region = 0; region < material.regionRamps.size(); ++region)
    {
        for (size_t stop = 0; stop < ModelColorRampStops; ++stop)
        {
            uint8_t *pPixel = &pixels[(region * ModelColorRampStops + stop) * 4];
            for (size_t channel = 0; channel < 3; ++channel)
            {
                const float encoded = linearToSrgb(material.regionRamps[region].colors[stop][channel]);
                pPixel[channel] = uint8_t(std::lround(std::clamp(encoded, 0.0f, 1.0f) * 255.0f));
            }
        }
    }
    const bgfx::TextureHandle texture = bgfx::createTexture2D(uint16_t(ModelColorRampStops),
        uint16_t(ModelMaxColorRegions), false, 1, bgfx::TextureFormat::RGBA8, BGFX_TEXTURE_SRGB,
        bgfx::copy(pixels.data(), uint32_t(pixels.size())));
    if (!bgfx::isValid(texture))
    {
        throw std::runtime_error("Cannot allocate model colour ramps: " + material.name);
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

// Static placement instance data: three affine matrix rows, then light, then point light and LOD crossfade.
constexpr uint16_t StaticInstanceStride = 5 * 4 * sizeof(float);
// Instanced skinned creature: ambient light and sun visibility, then the joint palette row (w).
constexpr uint16_t SkinnedInstanceStride = 2 * 4 * sizeof(float);

// u_modelEnvironment: sky reflection colour (the ambient light times the environment scale) and the cube's last mip.
std::array<float, 4> modelEnvironmentUniform(const ModelRenderLighting &lighting, float maxLod)
{
    std::array<float, 4> environment = {0, 0, 0, maxLod};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        environment[channel] = lighting.ambientColor[channel] * lighting.ambient * lighting.environmentScale[channel];
    }
    return environment;
}

// Lighting that instanced skinned draws share; the rest (ambient light and sun visibility) is per instance.
bool sameSharedLighting(const ModelRenderLighting &left, const ModelRenderLighting &right)
{
    return left.lightDirection == right.lightDirection && left.directColor == right.directColor
        && left.environmentScale == right.environmentScale
        && left.displaySpaceLighting == right.displaySpaceLighting && left.keyDirection == right.keyDirection
        && left.keyFraction == right.keyFraction;
}

// u_modelPbr.w: the specular scale, negated when the metallic-roughness red channel masks it per texel.
float modelSpecularUniform(const ModelMaterial &material)
{
    return material.specularMask ? -material.specular : material.specular;
}

float matrixScale(const ModelMatrix &matrix)
{
    return std::sqrt(matrix[0] * matrix[0] + matrix[1] * matrix[1] + matrix[2] * matrix[2]);
}

ModelBounds transformedBounds(const ModelBounds &bounds, const ModelMatrix &matrix)
{
    ModelBounds result;
    if (!bounds.valid)
    {
        return result;
    }
    for (uint32_t corner = 0; corner < 8; ++corner)
    {
        const std::array<float, 3> point = transformPoint(matrix, {
            (corner & 1) != 0 ? bounds.max[0] : bounds.min[0],
            (corner & 2) != 0 ? bounds.max[1] : bounds.min[1],
            (corner & 4) != 0 ? bounds.max[2] : bounds.min[2]});
        for (size_t axis = 0; axis < 3; ++axis)
        {
            result.min[axis] = result.valid ? std::min(result.min[axis], point[axis]) : point[axis];
            result.max[axis] = result.valid ? std::max(result.max[axis], point[axis]) : point[axis];
        }
        result.valid = true;
    }
    return result;
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

ModelBounds ModelStaticGroup::placementBounds(const ModelStaticPlacement &placement) const
{
    if (asset == nullptr)
    {
        return {};
    }
    float wind = 0.0f;
    for (const ModelMaterial &material : asset->materials)
    {
        wind = std::max(wind, material.wind);
    }
    ModelBounds placed = transformedBounds(asset->staticBounds, placement.matrix);
    const float sway = wind * matrixScale(placement.matrix);
    for (size_t axis = 0; axis < 2; ++axis)
    {
        placed.min[axis] -= sway;
        placed.max[axis] += sway;
    }
    return placed;
}

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

uint32_t ModelRenderer::jointPaletteRow(const Draw &draw)
{
    constexpr uint32_t JointsPerRow = 128;
    constexpr uint16_t PaletteWidth = JointsPerRow * 4;
    const ModelSkin &skin = *draw.pSkin;
    const uint32_t count = uint32_t(skin.joints.size());
    if (count == 0)
    {
        throw std::runtime_error("Skinned model has no joints");
    }
    const uint32_t rows = (count + JointsPerRow - 1) / JointsPerRow;
    JointSlot &slot = m_jointSlots[draw.pCullMatrix];
    if (slot.owner != draw.instance || slot.rows != rows)
    {
        releaseJointRows(slot.row, slot.rows);
        slot = {draw.instance};
    }
    if (slot.rows == 0)
    {
        // First fit; a full palette doubles. Rows other skins already used this frame stay valid: bgfx destroys the
        // old texture only after the frame, and every slot re-uploads into the new one.
        uint32_t row = 0;
        while (row + rows <= m_jointRowsUsed.size()
            && std::find(m_jointRowsUsed.begin() + row, m_jointRowsUsed.begin() + row + rows, 1)
                != m_jointRowsUsed.begin() + row + rows)
        {
            ++row;
        }
        if (row + rows > m_jointRowsUsed.size())
        {
            const uint32_t limit = bgfx::getCaps()->limits.maxTextureSize;
            uint32_t height = std::max<uint32_t>(64, uint32_t(m_jointRowsUsed.size()));
            while (height < row + rows)
            {
                height *= 2;
            }
            if (height > limit || PaletteWidth > limit
                || !bgfx::isTextureValid(0, false, 1, bgfx::TextureFormat::RGBA32F,
                    BGFX_SAMPLER_POINT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP))
            {
                throw std::runtime_error("GPU cannot hold the model joint palette");
            }
            if (bgfx::isValid(m_jointPalette))
            {
                bgfx::destroy(m_jointPalette);
            }
            m_jointPalette = bgfx::createTexture2D(PaletteWidth, uint16_t(height), false, 1,
                bgfx::TextureFormat::RGBA32F, BGFX_SAMPLER_POINT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            if (!bgfx::isValid(m_jointPalette))
            {
                throw std::runtime_error("Cannot allocate model joint palette");
            }
            m_jointRowsUsed.resize(height, 0);
            for (auto &[pMatrix, other] : m_jointSlots)
            {
                other.revision = 0;
            }
        }
        std::fill_n(m_jointRowsUsed.begin() + row, rows, 1);
        slot.row = row;
        slot.rows = rows;
        slot.revision = 0;
    }
    if (slot.revision != draw.pPose->matrixRevision || slot.revision == 0)
    {
        // Written straight into bgfx-owned memory: no per-frame allocation or extra copy.
        const uint16_t width = rows == 1 ? uint16_t(count * 4) : PaletteWidth;
        const bgfx::Memory *pMemory = bgfx::alloc(uint32_t(width) * rows * 4 * sizeof(float));
        std::fill_n(pMemory->data, pMemory->size, uint8_t(0));
        ModelMatrix *pMatrices = reinterpret_cast<ModelMatrix *>(pMemory->data);
        for (size_t index = 0; index < count; ++index)
        {
            pMatrices[index] = multiplyModelMatrices(
                draw.pPose->globalMatrices[skin.joints[index]], skin.inverseBindMatrices[index]);
        }
        bgfx::updateTexture2D(m_jointPalette, 0, 0, 0, uint16_t(slot.row), width, uint16_t(rows), pMemory);
        slot.revision = draw.pPose->matrixRevision;
    }
    return slot.row;
}

void ModelRenderer::releaseJointRows(uint32_t row, uint32_t rows)
{
    if (rows != 0 && row + rows <= m_jointRowsUsed.size())
    {
        std::fill_n(m_jointRowsUsed.begin() + row, rows, 0);
    }
}

uint64_t ModelRenderer::colorCullState(const ModelMaterial &material, const ModelMatrix &matrix) const
{
    return m_reflectionPass ? 0 : cullState(material, matrix);
}

void ModelRenderer::bindSkin(const Draw &draw)
{
    float params[4] = {};
    if (draw.pSkin != nullptr)
    {
        params[2] = float(jointPaletteRow(draw));
        params[0] = 1;
        params[1] = 1.0f / float(m_jointRowsUsed.size());
        bgfx::setTexture(5, m_skinSamplerHandle, m_jointPalette);
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
        lighting.directColor[0], lighting.directColor[1], lighting.directColor[2],
        lighting.displaySpaceLighting ? 1.0f : 0.0f,
        lighting.ambientColor[0], lighting.ambientColor[1], lighting.ambientColor[2], lighting.ambient,
        lighting.keyDirection[0] * lighting.keyFraction, lighting.keyDirection[1] * lighting.keyFraction,
        lighting.keyDirection[2] * lighting.keyFraction, float(std::min(lighting.pointCount, 12u)),
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
    const float pbr[4] = {material.metallic, material.roughness, material.translucency, modelSpecularUniform(material)};
    bgfx::setTexture(1, m_normalSamplerHandle, hasNormal ? textures.normal : m_whiteTextureHandle,
        samplerFlags(material.normalSampler));
    bgfx::setTexture(2, m_metallicRoughnessSamplerHandle,
        bgfx::isValid(textures.metallicRoughness) ? textures.metallicRoughness : m_whiteTextureHandle,
        samplerFlags(material.metallicRoughnessSampler));
    // Model uniforms persist between draws and the main/transparent views are sequential, so the next draw of the
    // same instance in the same view (e.g. a second material) keeps the instance's lighting uniforms.
    const bool sameInstance = m_lastSubmit.viewId == viewId && m_lastSubmit.instance == draw.instance
        && m_lastSubmit.pLighting == &lighting;
    m_lastSubmit = {viewId, draw.instance, &lighting};
    bgfx::setUniform(m_pbrUniformHandle, pbr);
    if (!sameInstance)
    {
        // The shader reads only the first pointCount entries.
        const uint16_t pointCount = uint16_t(std::clamp(lighting.pointCount, 1u, 12u));
        bgfx::setUniform(m_pointPositionsUniformHandle, lighting.pointPositions.data(), pointCount);
        bgfx::setUniform(m_pointColorsUniformHandle, lighting.pointColors.data(), pointCount);
        bgfx::setUniform(m_lightingUniformHandle, lightingValues, 4);
        bgfx::setUniform(m_normalMatrixUniformHandle, transformedNormals.data());
        const std::array<float, 4> environment = modelEnvironmentUniform(lighting, m_environmentMaxLod);
        bgfx::setUniform(m_environmentUniformHandle, environment.data());
    }
    bgfx::setUniform(m_surfaceUniformHandle, surface);
    bgfx::setUniform(m_materialUniformHandle, materialValues, 2);
    bindColorRegions(material, textures);
    bgfx::setTexture(3, m_environmentSamplerHandle, m_environmentTextureHandle);
    bgfx::setTexture(4, m_environmentBrdfSamplerHandle, m_environmentBrdfTextureHandle);
    if (hasSunShadows())
    {
        bindSunShadows();
    }
    const uint64_t state = material.alphaMode == ModelAlphaMode::Blend ? BlendState : OpaqueState;
    if (draw.outlineColorAbgr != 0 && !m_reflectionPass)
    {
        const float outline[4] = {float(draw.outlineColorAbgr & 255) / 255,
            float((draw.outlineColorAbgr >> 8) & 255) / 255, float((draw.outlineColorAbgr >> 16) & 255) / 255, 1};
        bgfx::setUniform(m_outlineUniformHandle, outline);
        bgfx::setState((OpaqueState & ~BGFX_STATE_WRITE_Z)
            | (determinant3x3(*draw.pCullMatrix) < 0 ? BGFX_STATE_CULL_CW : BGFX_STATE_CULL_CCW));
        bgfx::submit(viewId, m_programHandle, 0, BGFX_DISCARD_NONE);
    }
    if (!sameInstance || draw.outlineColorAbgr != 0)
    {
        const float noOutline[4] = {};
        bgfx::setUniform(m_outlineUniformHandle, noOutline);
    }
    bgfx::setState(state | colorCullState(material, *draw.pCullMatrix));
    bgfx::submit(viewId, m_programHandle);
}

void ModelRenderer::submitInstancedSkinned(std::vector<Draw> &draws, uint16_t viewId)
{
    // Palette rows first: allocating one may grow the palette, and every draw below reads the final texture.
    std::vector<uint32_t> rows(draws.size());
    for (size_t index = 0; index < draws.size(); ++index)
    {
        rows[index] = jointPaletteRow(draws[index]);
    }
    // One run per primitive, material and winding; inside a run the creatures stay in front-to-back order.
    std::vector<uint32_t> order(draws.size());
    for (uint32_t index = 0; index < order.size(); ++index)
    {
        order[index] = index;
    }
    const auto mirrored = [](const Draw &draw)
    {
        return determinant3x3(*draw.pCullMatrix) < 0;
    };
    const auto runKey = [&](uint32_t index)
    {
        const Draw &draw = draws[index];
        return std::make_tuple(draw.pPrimitive, draw.materialIndex, mirrored(draw));
    };
    std::stable_sort(order.begin(), order.end(), [&](uint32_t left, uint32_t right)
    {
        return runKey(left) < runKey(right);
    });

    const ModelRenderLighting &shared = *draws.front().pLighting;
    // Ambient and sun strength arrive per instance (v_color0), as on static placements.
    const float lightingValues[16] = {
        shared.lightDirection[0], shared.lightDirection[1], shared.lightDirection[2], 1.0f,
        shared.directColor[0], shared.directColor[1], shared.directColor[2],
        shared.displaySpaceLighting ? 1.0f : 0.0f,
        1.0f, 1.0f, 1.0f, 1.0f,
        shared.keyDirection[0] * shared.keyFraction, shared.keyDirection[1] * shared.keyFraction,
        shared.keyDirection[2] * shared.keyFraction, 0.0f,
    };
    const float environment[4] = {shared.environmentScale[0], shared.environmentScale[1], shared.environmentScale[2],
        m_environmentMaxLod};
    const float skin[4] = {1.0f, 1.0f / float(m_jointRowsUsed.size()), 0.0f, 0.0f};
    const float noOutline[4] = {};
    bgfx::setUniform(m_lightingUniformHandle, lightingValues, 4);
    bgfx::setUniform(m_environmentUniformHandle, environment);
    bgfx::setUniform(m_skinParamsHandle, skin);
    bgfx::setUniform(m_outlineUniformHandle, noOutline);
    std::vector<Draw> leftover;
    for (size_t first = 0; first < order.size();)
    {
        size_t end = first + 1;
        while (end < order.size() && runKey(order[end]) == runKey(order[first]))
        {
            ++end;
        }
        const uint32_t count = uint32_t(end - first);
        if (bgfx::getAvailInstanceDataBuffer(count, SkinnedInstanceStride) < count)
        {
            for (size_t slot = first; slot < end; ++slot)
            {
                leftover.push_back(draws[order[slot]]);
            }
            first = end;
            continue;
        }
        bgfx::InstanceDataBuffer buffer;
        bgfx::allocInstanceDataBuffer(&buffer, count, SkinnedInstanceStride);
        float *pData = reinterpret_cast<float *>(buffer.data);
        for (size_t slot = first; slot < end; ++slot)
        {
            const ModelRenderLighting &lighting = *draws[order[slot]].pLighting;
            for (size_t channel = 0; channel < 3; ++channel)
            {
                pData[channel] = lighting.ambientColor[channel] * lighting.ambient;
                pData[4 + channel] = 0.0f;
            }
            pData[3] = lighting.direct;
            pData[7] = float(rows[order[slot]]);
            pData += 8;
        }
        const Draw &draw = draws[order[first]];
        bindStaticMaterial(*draw.pResources, *draw.pMaterial, draw.materialIndex, 0.0f, false);
        bgfx::setTexture(3, m_environmentSamplerHandle, m_environmentTextureHandle);
        bgfx::setTexture(4, m_environmentBrdfSamplerHandle, m_environmentBrdfTextureHandle);
        bgfx::setTexture(5, m_skinSamplerHandle, m_jointPalette);
        if (hasSunShadows())
        {
            bindSunShadows();
        }
        bgfx::setVertexBuffer(0, draw.pPrimitive->skinnedVertexBuffer);
        bgfx::setIndexBuffer(draw.pPrimitive->indexBuffer, 0, draw.pPrimitive->indexCount);
        bgfx::setInstanceDataBuffer(&buffer);
        bgfx::setState(OpaqueState | colorCullState(*draw.pMaterial, *draw.pCullMatrix));
        bgfx::submit(viewId, m_skinnedInstancedProgramHandle);
        first = end;
    }
    m_lastSubmit = {};
    // Out of instance memory this frame: the rest draw one by one.
    for (const Draw &draw : leftover)
    {
        submit(draw, viewId, *draw.pLighting);
    }
}

void ModelRenderer::collectAttachments(const ModelInstanceSystem &instances)
{
    std::vector<ModelStaticGroup> groups;
    std::vector<std::vector<ModelInstanceHandle>> owners;
    std::vector<bool> standIns;
    const auto groupFor = [&](const std::shared_ptr<const ModelAsset> &asset, uint32_t variant, bool standIn)
    {
        size_t group = 0;
        while (group < groups.size() && (groups[group].asset != asset || groups[group].variant != variant))
        {
            ++group;
        }
        if (group == groups.size())
        {
            groups.push_back({asset, variant});
            owners.emplace_back();
            standIns.push_back(standIn);
            if (standIn)
            {
                groups.back().lodPixels = ModelStandInLodPixels;
            }
        }
        return group;
    };
    for (const ModelInstanceHandle handle : instances.handles())
    {
        if (!instances.isVisible(handle))
        {
            continue;
        }
        const std::shared_ptr<const ModelAsset> &standIn = instances.staticStandIn(handle);
        const ModelTransform *pRoot = instances.rootTransform(handle);
        if (standIn != nullptr && pRoot != nullptr)
        {
            const size_t group = groupFor(standIn, instances.materialVariant(handle), true);
            ModelStaticPlacement placement;
            placement.matrix = composeModelTransform(*pRoot);
            placement.outlineColorAbgr = instances.outlineColor(handle);
            placement.coverage = instances.coverage(handle);
            groups[group].bounds.push_back(groups[group].placementBounds(placement));
            groups[group].placements.push_back(placement);
            owners[group].push_back(handle);
        }
        for (const ModelAttachment &attachment : instances.attachments(handle))
        {
            const ModelMatrix *pMatrix = instances.nodeMatrix(handle, attachment.nodeIndex);
            if (pMatrix == nullptr || !modelMatrixVisible(*pMatrix))
            {
                continue;
            }
            const size_t group = groupFor(attachment.asset, attachment.materialVariant, false);
            ModelStaticPlacement placement;
            placement.matrix = *pMatrix;
            placement.outlineColorAbgr = instances.outlineColor(handle);
            placement.coverage = instances.coverage(handle);
            groups[group].bounds.push_back(groups[group].placementBounds(placement));
            groups[group].placements.push_back(placement);
            owners[group].push_back(handle);
        }
    }
    // Each carrier keeps its LOD hysteresis and crossfade from the previous frame's placement.
    for (size_t group = 0; group < groups.size(); ++group)
    {
        groups[group].lodLevels.resize(groups[group].placements.size());
        groups[group].fades.resize(groups[group].placements.size());
        for (size_t previous = 0; previous < m_attachmentGroups.size(); ++previous)
        {
            const ModelStaticGroup &old = m_attachmentGroups[previous];
            if (old.asset != groups[group].asset || old.variant != groups[group].variant)
            {
                continue;
            }
            std::unordered_map<uint32_t, size_t> oldSlots;
            for (size_t slot = 0; slot < m_attachmentOwners[previous].size() && slot < old.lodLevels.size(); ++slot)
            {
                const ModelInstanceHandle owner = m_attachmentOwners[previous][slot];
                oldSlots[owner.index] = slot;
            }
            for (size_t slot = 0; slot < owners[group].size(); ++slot)
            {
                const auto found = oldSlots.find(owners[group][slot].index);
                if (found != oldSlots.end() && m_attachmentOwners[previous][found->second] == owners[group][slot])
                {
                    groups[group].lodLevels[slot] = old.lodLevels[found->second];
                    if (found->second < old.fades.size())
                    {
                        groups[group].fades[slot] = old.fades[found->second];
                    }
                }
            }
        }
    }
    m_attachmentGroups = std::move(groups);
    m_attachmentOwners = std::move(owners);
    m_attachmentStandIns = std::move(standIns);
}

std::vector<ModelRenderer::StaticBatch> ModelRenderer::collectStaticBatches(
    const std::vector<ModelStaticGroup> &groups, const std::function<bool(const ModelBounds &)> &visibleBounds,
    const ModelLodView &view, float timeSeconds)
{
    std::vector<StaticBatch> batches;
    const bool shadow = view.shadowCascade >= 0;
    const size_t slot = shadow ? size_t(1 + view.shadowCascade) : 0;
    for (const ModelStaticGroup &group : groups)
    {
        const AssetResources *pResources = prepare(group.asset);
        if (pResources == nullptr || group.bounds.size() != group.placements.size())
        {
            continue;
        }
        group.lodLevels.resize(group.placements.size());
        group.fades.resize(group.placements.size());
        const ModelAsset &asset = *group.asset;
        for (uint32_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
        {
            const ModelNode &node = asset.nodes[nodeIndex];
            if (node.meshIndex < 0 || node.skinIndex >= 0 || size_t(node.meshIndex) >= pResources->meshes.size())
            {
                continue;
            }
            const ModelMesh &base = asset.meshes[node.meshIndex];
            const uint32_t count = uint32_t(base.lodMeshes.size() + 1);
            const size_t first = batches.size();
            for (uint32_t level = 0; level < count; ++level)
            {
                batches.push_back({&group, pResources, nodeIndex,
                    level == 0 ? uint32_t(node.meshIndex) : base.lodMeshes[level - 1], level, {}, {}});
            }
            for (uint32_t index = 0; index < group.placements.size(); ++index)
            {
                const ModelBounds &bounds = group.bounds[index];
                if (!group.placements[index].visible || !bounds.valid || (visibleBounds && !visibleBounds(bounds)))
                {
                    continue;
                }
                uint8_t keptLevel = group.lodLevels[index][slot];
                uint8_t &level = view.keepState ? keptLevel : group.lodLevels[index][slot];
                const uint8_t previous = level;
                const float pixels = shadow ? modelBoundsDiameter(bounds) * view.orthographicPixelsPerUnit
                    : modelProjectedPixels(bounds, view.camera, view.focalPixels);
                level = uint8_t(view.enabled && (shadow || view.focalPixels > 0)
                    ? modelLodLevel(pixels, level, count, shadow, group.lodPixels) : 0);
                if (!shadow && group.placements[index].colorLevel >= 0)
                {
                    level = uint8_t(std::min(uint32_t(group.placements[index].colorLevel), count - 1));
                }
                if (!shadow && view.forcedLevel >= 0)
                {
                    level = uint8_t(std::min(uint32_t(view.forcedLevel), count - 1));
                }
                // A dissolving placement casts its full shadow until it is gone.
                const float coverage = group.placements[index].coverage;
                if (coverage <= 0.0f)
                {
                    continue;
                }
                if (!shadow && coverage < 1.0f)
                {
                    batches[first + level].placements.push_back(index);
                    batches[first + level].fades.push_back(std::clamp(coverage, 0.001f, 0.999f));
                    continue;
                }
                float progress = 1.0f;
                if (!shadow && !view.keepState)
                {
                    // A level change crossfades from the level shown before; the first sight of a placement does not.
                    ModelStaticFade &fade = group.fades[index];
                    if (!fade.seen || view.forcedLevel >= 0)
                    {
                        fade = {level, true, -ModelStaticFadeSeconds};
                    }
                    else if (level != previous)
                    {
                        fade = {previous, true, timeSeconds};
                    }
                    progress = (timeSeconds - fade.startSeconds) / ModelStaticFadeSeconds;
                    if (fade.from != level && fade.from < count && progress >= 0.0f && progress < 1.0f)
                    {
                        const float shown = std::clamp(progress, 0.001f, 0.999f);
                        batches[first + fade.from].placements.push_back(index);
                        batches[first + fade.from].fades.push_back(1.0f + shown);
                        batches[first + level].placements.push_back(index);
                        batches[first + level].fades.push_back(shown);
                        continue;
                    }
                }
                batches[first + level].placements.push_back(index);
                batches[first + level].fades.push_back(0.0f);
            }
        }
    }
    std::erase_if(batches, [](const StaticBatch &batch) { return batch.placements.empty(); });
    return batches;
}

bool ModelRenderer::allocateStaticInstances(const StaticBatch &batch, const ModelMatrix &nodeMatrix,
    bgfx::InstanceDataBuffer &buffer) const
{
    const uint32_t count = uint32_t(batch.placements.size());
    if (count == 0 || bgfx::getAvailInstanceDataBuffer(count, StaticInstanceStride) < count)
    {
        return false;
    }
    bgfx::allocInstanceDataBuffer(&buffer, count, StaticInstanceStride);
    float *pData = reinterpret_cast<float *>(buffer.data);
    for (size_t slot = 0; slot < batch.placements.size(); ++slot)
    {
        const ModelStaticPlacement &placement = batch.pGroup->placements[batch.placements[slot]];
        const ModelMatrix matrix = multiplyModelMatrices(placement.matrix, nodeMatrix);
        for (size_t row = 0; row < 3; ++row)
        {
            pData[row * 4 + 0] = matrix[row];
            pData[row * 4 + 1] = matrix[4 + row];
            pData[row * 4 + 2] = matrix[8 + row];
            pData[row * 4 + 3] = matrix[12 + row];
        }
        std::copy(placement.light.begin(), placement.light.end(), pData + 12);
        std::copy(placement.pointLight.begin(), placement.pointLight.end(), pData + 16);
        pData[19] = slot < batch.fades.size() ? batch.fades[slot] : 0.0f;
        pData += 20;
    }
    return true;
}

void ModelRenderer::bindStaticMaterial(const AssetResources &resources, const ModelMaterial &material,
    int materialIndex, float timeSeconds, bool shadow)
{
    AssetResources::MaterialTextures textures;
    if (materialIndex >= 0)
    {
        textures = resources.materialTextures[materialIndex];
    }
    bgfx::setTexture(0, m_textureSamplerHandle, bgfx::isValid(textures.base) ? textures.base : m_whiteTextureHandle,
        samplerFlags(material.baseSampler));
    const float staticValues[12] = {timeSeconds, material.wind, resources.height, material.billboard ? 1.0f : 0.0f,
        material.uvScroll[0], material.uvScroll[1], material.flipbook[0], material.flipbook[1],
        material.flipbook[2], material.flutter, material.pulse[0], material.pulse[1]};
    bgfx::setUniform(m_staticUniformHandle, staticValues, 3);
    if (shadow)
    {
        const float mask[8] = {0, 0, 0, material.baseColor[3], material.alphaCutoff,
            material.alphaMode == ModelAlphaMode::Mask ? 1.0f : 0.0f, 0, 0};
        bgfx::setUniform(m_materialUniformHandle, mask, 2);
        return;
    }
    const float materialValues[8] = {
        material.baseColor[0], material.baseColor[1], material.baseColor[2], material.baseColor[3],
        material.alphaCutoff,
        material.alphaMode == ModelAlphaMode::Mask ? 1.0f : 0.0f,
        material.unlit ? 1.0f : 0.0f,
        material.doubleSided ? 1.0f : 0.0f,
    };
    const bool hasNormal = bgfx::isValid(textures.normal);
    const float surface[4] = {material.emissive[0], material.emissive[1], material.emissive[2],
        hasNormal ? material.normalScale : -1.0f};
    const float pbr[4] = {material.metallic, material.roughness, material.translucency, modelSpecularUniform(material)};
    bgfx::setTexture(1, m_normalSamplerHandle, hasNormal ? textures.normal : m_whiteTextureHandle,
        samplerFlags(material.normalSampler));
    bgfx::setTexture(2, m_metallicRoughnessSamplerHandle,
        bgfx::isValid(textures.metallicRoughness) ? textures.metallicRoughness : m_whiteTextureHandle,
        samplerFlags(material.metallicRoughnessSampler));
    bgfx::setUniform(m_materialUniformHandle, materialValues, 2);
    bgfx::setUniform(m_surfaceUniformHandle, surface);
    bgfx::setUniform(m_pbrUniformHandle, pbr);
    bindColorRegions(material, textures);
}

void ModelRenderer::bindColorRegions(
    const ModelMaterial &material, const AssetResources::MaterialTextures &textures) const
{
    // Rows 0/1: luminance range start/end per region (mask channel); row 2: 1 for each region with a ramp.
    float regions[12] = {0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0};
    const bool enabled = bgfx::isValid(textures.regionMask) && bgfx::isValid(textures.regionRamps);
    if (enabled)
    {
        for (size_t region = 0; region < material.regionRamps.size(); ++region)
        {
            regions[region] = material.regionRamps[region].luminanceRange[0];
            regions[4 + region] = material.regionRamps[region].luminanceRange[1];
            regions[8 + region] = 1.0f;
        }
    }
    bgfx::setUniform(m_regionUniformHandle, regions, 3);
    bgfx::setTexture(8, m_regionMaskSamplerHandle, enabled ? textures.regionMask : m_whiteTextureHandle,
        samplerFlags(material.regionMaskSampler));
    bgfx::setTexture(9, m_regionRampSamplerHandle, enabled ? textures.regionRamps : m_whiteTextureHandle,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIP_POINT);
}

void ModelRenderer::renderStatic(
    const std::vector<ModelStaticGroup> &groups,
    uint16_t viewId,
    const std::array<float, 3> &cameraPosition,
    const ModelRenderLighting &lighting,
    const ModelSkyEnvironment *pSkyEnvironment,
    const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
    float timeSeconds, uint16_t transparentView)
{
    if (!bgfx::isValid(m_staticProgramHandle) || groups.empty())
    {
        return;
    }
    m_staticDrawn = true;
    m_lastSubmit = {};
    prepareEnvironment(pSkyEnvironment);
    std::vector<StaticBatch> sorted = collectStaticBatches(groups, visibleBounds,
        {cameraPosition, focalPixels, 0, -1, true, forcedLod, m_reflectionPass}, timeSeconds);
    if (sorted.empty())
    {
        return;
    }
    const std::array<std::array<float, 4>, 3> fog = {lighting.fogColor, lighting.fogDensities, lighting.fogDistances};
    const float camera[4] = {cameraPosition[0], cameraPosition[1], cameraPosition[2], 0};
    const float lightingValues[16] = {
        lighting.lightDirection[0], lighting.lightDirection[1], lighting.lightDirection[2], lighting.direct,
        lighting.directColor[0], lighting.directColor[1], lighting.directColor[2],
        lighting.displaySpaceLighting ? 1.0f : 0.0f,
        lighting.ambientColor[0], lighting.ambientColor[1], lighting.ambientColor[2], lighting.ambient,
        lighting.keyDirection[0] * lighting.keyFraction, lighting.keyDirection[1] * lighting.keyFraction,
        lighting.keyDirection[2] * lighting.keyFraction, 0,
    };
    const std::array<float, 4> environment = modelEnvironmentUniform(lighting, m_environmentMaxLod);
    const float noOutline[4] = {};
    bgfx::setUniform(m_fogUniformHandle, fog.data(), 3);
    bgfx::setUniform(m_skyFogUniformHandle, lighting.skyFog.data(), uint16_t(lighting.skyFog.size()));
    bgfx::setUniform(m_cameraUniformHandle, camera);
    if (!hasSunShadows())
    {
        // Without shadow maps the shaders only read the (zero) enable flag; uniforms persist across draws, so it is
        // set once here instead of re-sending the shadow matrices and textures with every draw.
        bgfx::setUniform(m_shadowParamsUniformHandle, m_shadowParams.data(), 4);
    }
    bgfx::setUniform(m_lightingUniformHandle, lightingValues, 4);
    bgfx::setUniform(m_environmentUniformHandle, environment.data());
    // Nearest placements first inside each instanced draw, so depth testing rejects what they hide.
    for (StaticBatch &batch : sorted)
    {
        std::vector<std::pair<float, uint32_t>> order;
        order.reserve(batch.placements.size());
        for (uint32_t slot = 0; slot < batch.placements.size(); ++slot)
        {
            const ModelMatrix &matrix = batch.pGroup->placements[batch.placements[slot]].matrix;
            float distance = 0.0f;
            for (size_t axis = 0; axis < 3; ++axis)
            {
                distance += (matrix[12 + axis] - cameraPosition[axis]) * (matrix[12 + axis] - cameraPosition[axis]);
            }
            order.emplace_back(distance, slot);
        }
        std::sort(order.begin(), order.end());
        const std::vector<uint32_t> placements = batch.placements;
        const std::vector<float> fades = batch.fades;
        for (size_t slot = 0; slot < order.size(); ++slot)
        {
            batch.placements[slot] = placements[order[slot].second];
            batch.fades[slot] = fades[order[slot].second];
        }
    }
    std::vector<bgfx::InstanceDataBuffer> instanceData(sorted.size());
    std::vector<uint8_t> allocated(sorted.size(), 0);
    for (size_t index = 0; index < sorted.size(); ++index)
    {
        allocated[index] = allocateStaticInstances(sorted[index],
            sorted[index].pResources->restMatrices[sorted[index].nodeIndex], instanceData[index]) ? 1 : 0;
    }
    const auto materialFor = [](const StaticBatch &batch, size_t primitiveIndex, int &materialIndex)
        -> const ModelMaterial &
    {
        static const ModelMaterial defaultMaterial;
        const ModelAsset &asset = *batch.pGroup->asset;
        materialIndex = asset.meshes[batch.meshIndex].primitives[primitiveIndex].materialIndices[batch.pGroup->variant];
        return materialIndex >= 0 && size_t(materialIndex) < asset.materials.size()
            ? asset.materials[materialIndex] : defaultMaterial;
    };
    // Hover outlines first, without depth writes: the shell is pushed out along the normals (outline flag 2), and the
    // model drawn after it covers all but the rim.
    for (size_t index = 0; index < sorted.size() && !m_reflectionPass; ++index)
    {
        const StaticBatch &batch = sorted[index];
        for (size_t slot = 0; slot < batch.placements.size(); ++slot)
        {
            const ModelStaticPlacement &placement = batch.pGroup->placements[batch.placements[slot]];
            if (placement.outlineColorAbgr == 0 || (slot < batch.fades.size() && batch.fades[slot] > 1.0f))
            {
                continue;
            }
            StaticBatch single = batch;
            single.placements = {batch.placements[slot]};
            single.fades = {0.0f};
            bgfx::InstanceDataBuffer outlineInstance;
            if (!allocateStaticInstances(single, batch.pResources->restMatrices[batch.nodeIndex], outlineInstance))
            {
                continue;
            }
            const uint32_t color = placement.outlineColorAbgr;
            const float outline[4] = {float(color & 255) / 255, float((color >> 8) & 255) / 255,
                float((color >> 16) & 255) / 255, 2.0f};
            const MeshResources &mesh = batch.pResources->meshes[batch.meshIndex];
            for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
            {
                const PrimitiveResources &primitive = mesh.primitives[primitiveIndex];
                int materialIndex = -1;
                const ModelMaterial &material = materialFor(batch, primitiveIndex, materialIndex);
                if (material.alphaMode == ModelAlphaMode::Blend || !bgfx::isValid(primitive.vertexBuffer)
                    || !bgfx::isValid(primitive.indexBuffer))
                {
                    continue;
                }
                bindStaticMaterial(*batch.pResources, material, materialIndex, timeSeconds, false);
                bgfx::setUniform(m_outlineUniformHandle, outline);
                bgfx::setVertexBuffer(0, primitive.vertexBuffer);
                bgfx::setIndexBuffer(primitive.indexBuffer, 0, primitive.indexCount);
                bgfx::setInstanceDataBuffer(&outlineInstance);
                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_MSAA);
                bgfx::submit(viewId, m_staticProgramHandle);
            }
        }
    }
    // Alpha-tested foliage overlaps itself many times and its discard defeats early depth rejection. At the full
    // level (dense, large on screen) a depth-only prepass resolves the nearest surface with just the alpha test (the
    // outline flag returns right after it), and the shaded pass then tests equal depth without writing it, so each
    // pixel is shaded once; both passes use the same program, so their depths match exactly. The coarser levels are
    // smaller on screen and overlap less, where the extra pass costs more than it saves.
    const float depthOnly[4] = {0, 0, 0, 1};
    bgfx::setUniform(m_outlineUniformHandle, depthOnly);
    for (size_t index = 0; index < sorted.size(); ++index)
    {
        const StaticBatch &batch = sorted[index];
        const MeshResources &mesh = batch.pResources->meshes[batch.meshIndex];
        for (size_t primitiveIndex = 0; allocated[index] != 0 && primitiveIndex < mesh.primitives.size();
             ++primitiveIndex)
        {
            const PrimitiveResources &primitive = mesh.primitives[primitiveIndex];
            int materialIndex = -1;
            const ModelMaterial &material = materialFor(batch, primitiveIndex, materialIndex);
            if (material.alphaMode != ModelAlphaMode::Mask || batch.level != 0 || !m_staticFoliageVisible
                || m_reflectionPass
                || !bgfx::isValid(primitive.vertexBuffer)
                || !bgfx::isValid(primitive.indexBuffer))
            {
                continue;
            }
            bindStaticMaterial(*batch.pResources, material, materialIndex, timeSeconds, false);
            bgfx::setVertexBuffer(0, primitive.vertexBuffer);
            bgfx::setIndexBuffer(primitive.indexBuffer, 0, primitive.indexCount);
            bgfx::setInstanceDataBuffer(&instanceData[index]);
            bgfx::setState(BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_MSAA
                | cullState(material, batch.pGroup->placements[batch.placements.front()].matrix));
            bgfx::submit(viewId, m_staticProgramHandle);
        }
    }
    bgfx::setUniform(m_outlineUniformHandle, noOutline);
    constexpr uint64_t PrepassedState = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_EQUAL
        | BGFX_STATE_MSAA;
    for (size_t index = 0; index < sorted.size(); ++index)
    {
        const StaticBatch &batch = sorted[index];
        const MeshResources &mesh = batch.pResources->meshes[batch.meshIndex];
        for (size_t primitiveIndex = 0; allocated[index] != 0 && primitiveIndex < mesh.primitives.size();
             ++primitiveIndex)
        {
            const PrimitiveResources &primitive = mesh.primitives[primitiveIndex];
            if (!bgfx::isValid(primitive.vertexBuffer) || !bgfx::isValid(primitive.indexBuffer))
            {
                continue;
            }
            int materialIndex = -1;
            const ModelMaterial &material = materialFor(batch, primitiveIndex, materialIndex);
            if (!m_staticFoliageVisible && material.alphaMode == ModelAlphaMode::Mask)
            {
                continue;
            }
            bindStaticMaterial(*batch.pResources, material, materialIndex, timeSeconds, false);
            bgfx::setTexture(3, m_environmentSamplerHandle, m_environmentTextureHandle);
            bgfx::setTexture(4, m_environmentBrdfSamplerHandle, m_environmentBrdfTextureHandle);
            if (hasSunShadows())
            {
                bindSunShadows();
            }
            bgfx::setVertexBuffer(0, primitive.vertexBuffer);
            bgfx::setIndexBuffer(primitive.indexBuffer, 0, primitive.indexCount);
            bgfx::setInstanceDataBuffer(&instanceData[index]);
            const bool prepassed = material.alphaMode == ModelAlphaMode::Mask && batch.level == 0 && !m_reflectionPass;
            const uint64_t state = material.alphaMode == ModelAlphaMode::Blend ? BlendState
                : prepassed ? PrepassedState : OpaqueState;
            bgfx::setState(state
                | colorCullState(material, batch.pGroup->placements[batch.placements.front()].matrix));
            // Alpha-tested materials shade with the discard-free program: the prepass depth already holds the cutout.
            const uint16_t submitView = material.alphaMode == ModelAlphaMode::Blend && transparentView != UINT16_MAX
                ? transparentView : viewId;
            bgfx::submit(submitView, prepassed ? m_staticPrepassedProgramHandle : m_staticProgramHandle);
        }
    }
    m_lastSubmit = {};
}

void ModelRenderer::renderReflection(const ModelInstanceSystem &instances,
    const std::vector<ModelStaticGroup> &staticGroups, uint16_t viewId, const std::array<float, 3> &cameraPosition,
    const ModelRenderLighting &staticLighting, const ModelRenderLighting &lighting,
    const std::function<ModelRenderLighting(ModelInstanceHandle, const ModelBounds &)> &lightingForBounds,
    const ModelSkyEnvironment *pSkyEnvironment, const std::function<bool(const ModelBounds &)> &visibleBounds,
    float focalPixels, float timeSeconds)
{
    m_reflectionPass = true;
    renderStatic(staticGroups, viewId, cameraPosition, staticLighting, pSkyEnvironment, visibleBounds, focalPixels, -1,
        timeSeconds);
    render(instances, viewId, cameraPosition, lighting, lightingForBounds, pSkyEnvironment, visibleBounds,
        focalPixels, -1, viewId);
    m_reflectionPass = false;
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
            bindColorRegions(ModelMaterial{}, AssetResources::MaterialTextures{});
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

bool ModelRenderer::initialize(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle,
    bgfx::ProgramHandle skinnedInstancedProgramHandle)
{
    if (!bgfx::isValid(programHandle) || !BgfxContext::isBgfxInitialized())
    {
        return false;
    }
    shutdown(true);
    m_programHandle = programHandle;
    m_shadowProgramHandle = shadowProgramHandle;
    if ((bgfx::getCaps()->supported & BGFX_CAPS_INSTANCING) != 0)
    {
        m_skinnedInstancedProgramHandle = skinnedInstancedProgramHandle;
    }
    else if (bgfx::isValid(skinnedInstancedProgramHandle))
    {
        bgfx::destroy(skinnedInstancedProgramHandle);
    }
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
    m_skyFogUniformHandle = bgfx::createUniform("u_skyFog", bgfx::UniformType::Vec4, ModelSkyFogVectors);
    m_cameraUniformHandle = bgfx::createUniform("u_modelCamera", bgfx::UniformType::Vec4);
    m_outlineUniformHandle = bgfx::createUniform("u_modelOutline", bgfx::UniformType::Vec4);
    m_textureSamplerHandle = bgfx::createUniform("s_modelTexture", bgfx::UniformType::Sampler);
    m_materialUniformHandle = bgfx::createUniform("u_modelMaterial", bgfx::UniformType::Vec4, 2);
    m_regionUniformHandle = bgfx::createUniform("u_modelRegion", bgfx::UniformType::Vec4, 3);
    m_regionMaskSamplerHandle = bgfx::createUniform("s_modelRegionMask", bgfx::UniformType::Sampler);
    m_regionRampSamplerHandle = bgfx::createUniform("s_modelRegionRamp", bgfx::UniformType::Sampler);
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
        bgfx::isValid(m_fogUniformHandle) && bgfx::isValid(m_skyFogUniformHandle)
        && bgfx::isValid(m_cameraUniformHandle)
        && bgfx::isValid(m_outlineUniformHandle) &&
        bgfx::isValid(m_textureSamplerHandle) && bgfx::isValid(m_materialUniformHandle) &&
        bgfx::isValid(m_regionUniformHandle) && bgfx::isValid(m_regionMaskSamplerHandle)
        && bgfx::isValid(m_regionRampSamplerHandle) &&
        bgfx::isValid(m_lightingUniformHandle) && bgfx::isValid(m_normalMatrixUniformHandle) &&
        bgfx::isValid(m_whiteTextureHandle);
    if (!initialized)
    {
        shutdown(true);
    }
    return initialized;
}

bool ModelRenderer::initializeStatic(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle,
    bgfx::ProgramHandle prepassedProgramHandle)
{
    if (!bgfx::isValid(m_programHandle) || !bgfx::isValid(programHandle) || !bgfx::isValid(shadowProgramHandle)
        || !bgfx::isValid(prepassedProgramHandle) || (bgfx::getCaps()->supported & BGFX_CAPS_INSTANCING) == 0)
    {
        for (const bgfx::ProgramHandle handle : {programHandle, shadowProgramHandle, prepassedProgramHandle})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
        return false;
    }
    m_staticProgramHandle = programHandle;
    m_staticShadowProgramHandle = shadowProgramHandle;
    m_staticPrepassedProgramHandle = prepassedProgramHandle;
    m_staticUniformHandle = bgfx::createUniform("u_modelStatic", bgfx::UniformType::Vec4, 3);
    return bgfx::isValid(m_staticUniformHandle);
}

void ModelRenderer::preloadStatic(const std::vector<ModelStaticGroup> &groups)
{
    if (!bgfx::isValid(m_staticProgramHandle))
    {
        return;
    }
    for (const ModelStaticGroup &group : groups)
    {
        prepare(group.asset);
    }
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
        if (bgfx::isValid(m_skyFogUniformHandle))
        {
            bgfx::destroy(m_skyFogUniformHandle);
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
        for (const bgfx::UniformHandle handle :
            {m_regionUniformHandle, m_regionMaskSamplerHandle, m_regionRampSamplerHandle})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
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
        for (const bgfx::ProgramHandle handle :
            {m_staticProgramHandle, m_staticShadowProgramHandle, m_staticPrepassedProgramHandle,
                m_skinnedInstancedProgramHandle})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
        if (bgfx::isValid(m_staticUniformHandle))
        {
            bgfx::destroy(m_staticUniformHandle);
        }
    }
    m_assets.clear();
    m_sharedTextures.clear();
    m_programHandle = BGFX_INVALID_HANDLE;
    m_shadowProgramHandle = BGFX_INVALID_HANDLE;
    m_staticProgramHandle = BGFX_INVALID_HANDLE;
    m_staticShadowProgramHandle = BGFX_INVALID_HANDLE;
    m_staticPrepassedProgramHandle = BGFX_INVALID_HANDLE;
    m_skinnedInstancedProgramHandle = BGFX_INVALID_HANDLE;
    m_staticUniformHandle = BGFX_INVALID_HANDLE;
    m_shadowSamplers = {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    m_shadowMatricesUniformHandle = BGFX_INVALID_HANDLE;
    m_shadowParamsUniformHandle = BGFX_INVALID_HANDLE;
    m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    m_materialUniformHandle = BGFX_INVALID_HANDLE;
    m_regionUniformHandle = BGFX_INVALID_HANDLE;
    m_regionMaskSamplerHandle = BGFX_INVALID_HANDLE;
    m_regionRampSamplerHandle = BGFX_INVALID_HANDLE;
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
    m_skyFogUniformHandle = BGFX_INVALID_HANDLE;
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
    m_lastSubmit = {};
    m_staticDrawn = false;
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
        if (bgfx::isValid(m_jointPalette))
        {
            bgfx::destroy(m_jointPalette);
        }
    }
    m_deformedVertexBuffers.clear();
    m_jointSlots.clear();
    m_jointRowsUsed.clear();
    m_jointPalette = BGFX_INVALID_HANDLE;
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
    int quality, bool lods, const std::vector<ModelStaticGroup> *pStaticGroups, float timeSeconds)
{
    const ModelShadowSettings settings = modelShadowSettings(quality);
    m_shadowParams[0][0] = 0;
    const float lengthSquared = lightDirection[0] * lightDirection[0] + lightDirection[1] * lightDirection[1]
        + lightDirection[2] * lightDirection[2];
    collectAttachments(instances);
    const bool attachmentCasters = !m_attachmentGroups.empty() && bgfx::isValid(m_staticShadowProgramHandle);
    const bool staticCasters = pStaticGroups != nullptr && !pStaticGroups->empty()
        && bgfx::isValid(m_staticShadowProgramHandle);
    if (!enabled || settings.size == 0 || !bgfx::isValid(m_shadowProgramHandle)
        || (instances.size() == 0 && !staticCasters)
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
    std::array<std::vector<StaticBatch>, ModelSunShadowCascades> staticBatches;
    for (size_t index = 0; index < cascades.size(); ++index)
    {
        const auto inCascade = [&](const ModelBounds &bounds)
        {
            return modelSunShadowIntersects(cascades[index], bounds);
        };
        const ModelLodView cascadeView = {cameraPosition, 0, settings.size / (2.0f * settings.radii[index]),
            int(index), lods};
        if (staticCasters)
        {
            staticBatches[index] = collectStaticBatches(*pStaticGroups, inCascade, cascadeView, timeSeconds);
        }
        if (attachmentCasters)
        {
            std::vector<StaticBatch> carried = collectStaticBatches(m_attachmentGroups, inCascade, cascadeView,
                timeSeconds);
            staticBatches[index].insert(staticBatches[index].end(), carried.begin(), carried.end());
        }
    }
    if (cascadeDraws[0].empty() && cascadeDraws[1].empty() && staticBatches[0].empty() && staticBatches[1].empty())
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
        for (const StaticBatch &batch : staticBatches[index])
        {
            const ModelStaticGroup &group = *batch.pGroup;
            bgfx::InstanceDataBuffer instanceData;
            if (!allocateStaticInstances(batch, batch.pResources->restMatrices[batch.nodeIndex], instanceData))
            {
                continue;
            }
            const MeshResources &mesh = batch.pResources->meshes[batch.meshIndex];
            for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives.size(); ++primitiveIndex)
            {
                const PrimitiveResources &primitive = mesh.primitives[primitiveIndex];
                const int materialIndex =
                    group.asset->meshes[batch.meshIndex].primitives[primitiveIndex].materialIndices[group.variant];
                if (materialIndex < 0 || size_t(materialIndex) >= group.asset->materials.size()
                    || !bgfx::isValid(primitive.vertexBuffer) || !bgfx::isValid(primitive.indexBuffer))
                {
                    continue;
                }
                const ModelMaterial &material = group.asset->materials[materialIndex];
                // Camera-facing impostors would cast a camera-dependent shadow; far LODs simply cast none.
                if (material.alphaMode == ModelAlphaMode::Blend || material.billboard)
                {
                    continue;
                }
                bindStaticMaterial(*batch.pResources, material, materialIndex, timeSeconds, true);
                bgfx::setVertexBuffer(0, primitive.vertexBuffer);
                bgfx::setIndexBuffer(primitive.indexBuffer, 0, primitive.indexCount);
                bgfx::setInstanceDataBuffer(&instanceData);
                bgfx::setState((OpaqueState & ~BGFX_STATE_MSAA)
                    | cullState(material, group.placements[batch.placements.front()].matrix));
                bgfx::submit(viewId, m_staticShadowProgramHandle);
            }
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
    std::erase_if(m_jointSlots, [&](const auto &entry)
    {
        if (instances.contains(entry.second.owner) && instances.staticStandIn(entry.second.owner) == nullptr)
        {
            return false;
        }
        releaseJointRows(entry.second.row, entry.second.rows);
        return true;
    });
    static const ModelMaterial defaultMaterial;
    if (view.shadowCascade < 0 && !view.keepState)
    {
        m_instanceColorLevels.clear();
    }
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
        if (instances.staticStandIn(handle) != nullptr)
        {
            continue;   // drawn as a static placement by collectAttachments
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
            uint32_t keptLevel = shadow ? state.shadow[size_t(view.shadowCascade)] : state.color;
            uint32_t &level = view.keepState ? keptLevel
                : shadow ? state.shadow[size_t(view.shadowCascade)] : state.color;
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
            if (!shadow && !view.keepState)
            {
                uint32_t &carried = m_instanceColorLevels[handle.index];
                carried = std::max(carried, level);
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
    const std::function<ModelRenderLighting(ModelInstanceHandle, const ModelBounds &)> &lightingForBounds,
    const ModelSkyEnvironment *pSkyEnvironment,
    const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
    uint16_t transparentView)
{
    if (!bgfx::isValid(m_programHandle))
    {
        return;
    }
    if (instances.size() == 0 && m_reflectionPass)
    {
        return;
    }
    if (instances.size() == 0)
    {
        pruneUnusedAssets();
        destroyDeformedBuffers(true);
        if (!m_staticDrawn)
        {
            destroyEnvironment(true);
        }
        return;
    }
    m_lastSubmit = {};
    const std::array<std::array<float, 4>, 3> fog = {lighting.fogColor, lighting.fogDensities, lighting.fogDistances};
    const float camera[4] = {cameraPosition[0], cameraPosition[1], cameraPosition[2], 0};
    bgfx::setUniform(m_fogUniformHandle, fog.data(), 3);
    bgfx::setUniform(m_skyFogUniformHandle, lighting.skyFog.data(), uint16_t(lighting.skyFog.size()));
    bgfx::setUniform(m_cameraUniformHandle, camera);
    if (!hasSunShadows())
    {
        // Without shadow maps the shaders only read the (zero) enable flag; uniforms persist across draws, so it is
        // set once here instead of re-sending the shadow matrices and textures with every draw.
        bgfx::setUniform(m_shadowParamsUniformHandle, m_shadowParams.data(), 4);
    }
    std::unordered_map<uint32_t, ModelRenderLighting> instanceLighting;
    std::vector<Draw> opaqueDraws;
    std::vector<Draw> transparentDraws;
    // Scene consumers own the environment, even outside the camera. Loading renders prewarm it too.
    prepareEnvironment(pSkyEnvironment);
    std::vector<Draw> draws = collectDraws(instances, visibleBounds,
        {cameraPosition, focalPixels, 0, -1, true, forcedLod, m_reflectionPass});
    for (Draw &draw : draws)
    {
        auto found = instanceLighting.find(draw.instance.index);
        if (found == instanceLighting.end())
        {
            const ModelBounds *pBounds = instances.cullingBounds(draw.instance);
            found = instanceLighting.emplace(draw.instance.index,
                lightingForBounds && pBounds != nullptr ? lightingForBounds(draw.instance, *pBounds) : lighting).first;
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

    // Opaque draws: front to back by instance, with an instance's primitives adjacent (shared lighting uniforms).
    std::unordered_map<uint32_t, float> instanceDistance;
    for (const Draw &draw : opaqueDraws)
    {
        auto [found, inserted] = instanceDistance.emplace(draw.instance.index, draw.distanceSquared);
        found->second = std::min(found->second, draw.distanceSquared);
    }
    std::stable_sort(
        opaqueDraws.begin(),
        opaqueDraws.end(),
        [&](const Draw &left, const Draw &right)
        {
            const float leftDistance = instanceDistance[left.instance.index];
            const float rightDistance = instanceDistance[right.instance.index];
            return leftDistance != rightDistance ? leftDistance < rightDistance
                : left.instance.index < right.instance.index;
        });
    std::stable_sort(
        transparentDraws.begin(),
        transparentDraws.end(),
        [](const Draw &left, const Draw &right)
        {
            return left.distanceSquared > right.distanceSquared;
        });
    // The instanced draws bind materials like static placements, so they also need the static programs' uniforms.
    if (bgfx::isValid(m_skinnedInstancedProgramHandle) && bgfx::isValid(m_staticUniformHandle) && m_skinnedInstancing)
    {
        // Skinned creatures lit only by the shared sun and their own ambient draw instanced; point-lit, outlined
        // and morphing ones keep their own draws (directional point lights and outline shells are per draw).
        std::vector<Draw> instanced;
        std::vector<Draw> single;
        for (const Draw &draw : opaqueDraws)
        {
            const bool eligible = draw.pSkin != nullptr && draw.outlineColorAbgr == 0
                && draw.pLighting->pointCount == 0
                && (instanced.empty() || sameSharedLighting(*instanced.front().pLighting, *draw.pLighting));
            (eligible ? instanced : single).push_back(draw);
        }
        if (!instanced.empty())
        {
            submitInstancedSkinned(instanced, viewId);
        }
        opaqueDraws = std::move(single);
    }
    for (const Draw &draw : opaqueDraws)
    {
        submit(draw, viewId, *draw.pLighting);
    }
    collectAttachments(instances);
    if (!m_attachmentGroups.empty() && bgfx::isValid(m_staticProgramHandle))
    {
        // Each attachment takes its carrier's light (ambient, sun visibility, and its point lights as undirected
        // light at the attachment) and colour LOD level.
        const ModelRenderLighting *pShared = nullptr;
        for (size_t group = 0; group < m_attachmentGroups.size(); ++group)
        {
            for (size_t slot = 0; slot < m_attachmentGroups[group].placements.size(); ++slot)
            {
                const ModelInstanceHandle owner = m_attachmentOwners[group][slot];
                auto found = instanceLighting.find(owner.index);
                if (found == instanceLighting.end())
                {
                    const ModelBounds *pBounds = instances.cullingBounds(owner);
                    found = instanceLighting.emplace(owner.index, lightingForBounds && pBounds != nullptr
                        ? lightingForBounds(owner, *pBounds) : lighting).first;
                }
                const ModelRenderLighting &carrier = found->second;
                pShared = pShared != nullptr ? pShared : &carrier;
                ModelStaticPlacement &placement = m_attachmentGroups[group].placements[slot];
                const std::array<float, 3> position = {placement.matrix[12], placement.matrix[13],
                    placement.matrix[14]};
                for (size_t channel = 0; channel < 3; ++channel)
                {
                    placement.light[channel] = carrier.ambientColor[channel] * carrier.ambient;
                }
                placement.light[3] = carrier.direct;
                for (uint32_t light = 0; light < std::min(carrier.pointCount, 12u); ++light)
                {
                    float distanceSquared = 0.0f;
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        const float delta = carrier.pointPositions[light * 4 + axis] - position[axis];
                        distanceSquared += delta * delta;
                    }
                    const float radius = std::max(carrier.pointPositions[light * 4 + 3], 0.0001f);
                    const float attenuation = std::max(1.0f - distanceSquared / (radius * radius), 0.0f);
                    for (size_t channel = 0; channel < 3; ++channel)
                    {
                        placement.pointLight[channel] += carrier.pointColors[light * 4 + channel]
                            * carrier.pointColors[light * 4 + 3] * attenuation * attenuation;
                    }
                }
                const auto level = m_instanceColorLevels.find(owner.index);
                placement.colorLevel = !m_attachmentStandIns[group] && level != m_instanceColorLevels.end()
                    ? int32_t(level->second) : -1;   // a stand-in picks its own level by projected size
            }
        }
        ModelRenderLighting shared = *pShared;
        shared.ambient = 1.0f;
        shared.ambientColor = {1.0f, 1.0f, 1.0f};
        shared.direct = 1.0f;
        shared.pointCount = 0;
        renderStatic(m_attachmentGroups, viewId, cameraPosition, shared, pSkyEnvironment, visibleBounds, focalPixels,
            forcedLod, float(std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch())
                .count() - m_attachmentClockOrigin), transparentView);
    }
    for (const Draw &draw : transparentDraws)
    {
        submit(draw, transparentView == UINT16_MAX ? viewId : transparentView, *draw.pLighting);
    }
    for (const ModelInstanceHandle handle : instances.handles())
    {
        if (!m_reflectionPass && instances.isVisible(handle) && instances.areNodeMarkersVisible(handle))
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
        const ModelImage &image = asset->images.at(imageIndex);
        const std::string_view bytes(reinterpret_cast<const char *>(image.bytes.data()), image.bytes.size());
        const uint64_t key = (std::hash<std::string_view>()(bytes) ^ (uint64_t(bytes.size()) * 0x9e3779b97f4a7c15ull))
            + (uint64_t(semantic) << 56) + (uint64_t(alphaCutoff) << 48) + (mips ? 1ull << 47 : 0) + 1;
        SharedTexture &shared = m_sharedTextures[key];
        if (!bgfx::isValid(shared.handle))
        {
            shared.handle = createTexture(image, semantic, alphaCutoff, mips);
        }
        ++shared.references;
        resources.textures.push_back({imageIndex, int(semantic), alphaCutoff, mips, shared.handle, key});
        return shared.handle;
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
                textureFor(material.regionMaskImageIndex, ImageMipSemantic::Linear, 0, material.regionMaskSampler),
                createRampTexture(material),
            });
            if (bgfx::isValid(resources.materialTextures.back().regionRamps))
            {
                // Not an image: listed for destruction only (imageIndex -1 never matches a lookup).
                resources.textures.push_back({-1, 0, 0, false, resources.materialTextures.back().regionRamps});
            }
        }
    }
    catch (...)
    {
        destroy(resources);
        throw;
    }
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
                std::vector<ColoredVertex> colored(primitive.vertices.size());
                for (size_t index = 0; index < colored.size(); ++index)
                {
                    colored[index] = {primitive.vertices[index],
                        primitive.colors.empty() ? std::array<uint8_t, 4>{255, 255, 255, 255} : primitive.colors[index]};
                }
                primitiveResources.vertexBuffer = bgfx::createVertexBuffer(
                    bgfx::copy(colored.data(), uint32_t(colored.size() * sizeof(ColoredVertex))), coloredVertexLayout());
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
    ModelPose rest;
    resetModelPose(*asset, rest);
    evaluateModelHierarchy(*asset, identityModelMatrix(), rest);
    resources.restMatrices = rest.globalMatrices;
    resources.height = asset->staticBounds.valid ? asset->staticBounds.max[1] - asset->staticBounds.min[1] : 0.0f;
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
        if (texture.sharedKey != 0)
        {
            const auto shared = m_sharedTextures.find(texture.sharedKey);
            if (shared != m_sharedTextures.end() && --shared->second.references == 0)
            {
                bgfx::destroy(shared->second.handle);
                m_sharedTextures.erase(shared);
            }
        }
        else if (bgfx::isValid(texture.handle))
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
