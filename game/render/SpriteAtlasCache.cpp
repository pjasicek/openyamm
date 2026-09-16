#include "game/render/SpriteAtlasCache.h"

#include "engine/ImageAssetLoader.h"
#include "game/render/TextureFiltering.h"
#include "game/render/SpriteAtlasMipmaps.h"
#include "game/tables/SpriteTables.h"

#include <iostream>
#include <cmath>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Game
{
void SpriteAtlasCache::setProgram(bgfx::ProgramHandle program)
{
    m_program = program;
}

bool SpriteAtlasCache::load(const Engine::AssetFileSystem &assets, const std::string &name, int16_t variant,
    SpriteBillboardTexture &texture)
{
    const std::string key = name + ":" + std::to_string(variant);
    if (m_failed.contains(key))
    {
        return false;
    }
    try
    {
        const std::optional<Engine::SpriteAtlasReference> reference = Engine::parseSpriteAtlasReference(name);
        if (!reference || !bgfx::isValid(m_program))
        {
            throw std::runtime_error("Invalid atlas reference or unavailable atlas shader");
        }
        const std::string root = "engine/sprites_new/" + reference->package + "/";
        if (!m_packages.contains(reference->package))
        {
            const std::optional<std::string> text = assets.readTextFile(root + "manifest.json");
            std::string error;
            const std::optional<Engine::SpriteAtlas> atlas = text
                ? Engine::SpriteAtlas::parse(*text, error) : std::nullopt;
            if (!atlas)
            {
                throw std::runtime_error("Cannot load " + root + "manifest.json: " + error);
            }
            Package package;
            package.atlas = *atlas;
            package.pages.resize(atlas->pages.size());
            m_packages.emplace(reference->package, std::move(package));
        }
        Package &package = m_packages.at(reference->package);
        const Engine::SpriteAtlas &atlas = package.atlas;
        if (!atlas.frames.contains(reference->frame) || !atlas.variants.contains(variant))
        {
            throw std::runtime_error("Atlas frame or variant is not declared");
        }
        const Engine::SpriteAtlasFrame &frame = atlas.frames.at(reference->frame);
        const Engine::SpriteAtlasVariant &appearance = atlas.variants.at(variant);
        if (!appearance.lookup.empty() && !package.lookups.contains(variant))
        {
            const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(root + appearance.lookup);
            const size_t expected = size_t(appearance.lookupSize[0]) * appearance.lookupSize[1] * 4 * sizeof(float);
            if (!bytes || bytes->size() != expected)
            {
                throw std::runtime_error("Invalid sprite lookup byte count: " + appearance.lookup);
            }
            for (size_t offset = 0; offset < expected; offset += sizeof(float))
            {
                float value;
                std::memcpy(&value, bytes->data() + offset, sizeof(float));
                if (!std::isfinite(value) || std::abs(value) > 64)
                {
                    throw std::runtime_error("Invalid sprite lookup value: " + appearance.lookup);
                }
            }
            const bgfx::TextureHandle lookup = bgfx::createTexture2D(
                uint16_t(appearance.lookupSize[0]), uint16_t(appearance.lookupSize[1]), false, 1,
                bgfx::TextureFormat::RGBA32F, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
                    | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
                bgfx::copy(bytes->data(), uint32_t(bytes->size())));
            if (!bgfx::isValid(lookup))
            {
                throw std::runtime_error("Unable to allocate sprite palette lookup");
            }
            package.lookups.emplace(variant, lookup);
        }
        const Engine::SpriteAtlasPage &description = atlas.pages[frame.page];
        Page &page = package.pages[frame.page];
        if (!bgfx::isValid(page.base))
        {
            const auto decode = [&](const std::string &path)
            {
                const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(root + path);
                std::optional<Engine::ImagePixelsBgra> image = bytes
                    ? Engine::decodeImagePixelsBgra(*bytes, path) : std::nullopt;
                if (!image || image->width != description.size[0] || image->height != description.size[1])
                {
                    throw std::runtime_error("Atlas page dimensions or image invalid: " + path);
                }
                return std::move(*image);
            };
            const Engine::ImagePixelsBgra base = decode(description.base);
            const Engine::ImagePixelsBgra mask = decode(description.mask);
            SpriteAtlasMipPage mipPage = buildSpriteAtlasMipPage(atlas, frame.page,
                base.pixels, mask.pixels, bgfx::getCaps()->limits.maxTextureSize);
            page.size = {mipPage.levels.front().width, mipPage.levels.front().height};
            page.rectangles = std::move(mipPage.rectangles);
            page.base = bgfx::createTexture2D(uint16_t(page.size[0]), uint16_t(page.size[1]), true, 1,
                bgraTextureUploadFormat(), BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            page.mask = bgfx::createTexture2D(uint16_t(page.size[0]), uint16_t(page.size[1]), true, 1,
                atlas.maskChannels == 4 ? bgfx::TextureFormat::RGBA8
                    : (atlas.maskChannels == 2 ? bgfx::TextureFormat::RG8 : bgfx::TextureFormat::R8),
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            if (!bgfx::isValid(page.base) || !bgfx::isValid(page.mask))
            {
                if (bgfx::isValid(page.base))
                {
                    bgfx::destroy(page.base);
                }
                if (bgfx::isValid(page.mask))
                {
                    bgfx::destroy(page.mask);
                }
                page.base = BGFX_INVALID_HANDLE;
                page.mask = BGFX_INVALID_HANDLE;
                throw std::runtime_error("Unable to allocate atlas base/mask textures");
            }
            for (uint8_t mip = 0; mip < mipPage.levels.size(); ++mip)
            {
                const SpriteAtlasMipLevel &level = mipPage.levels[mip];
                bgfx::updateTexture2D(page.base, 0, mip, 0, 0, uint16_t(level.width), uint16_t(level.height),
                    copyBgraTextureUploadMemory(level.baseBgra.data(), uint32_t(level.baseBgra.size())));
                bgfx::updateTexture2D(page.mask, 0, mip, 0, 0, uint16_t(level.width), uint16_t(level.height),
                    bgfx::copy(level.mask.data(), uint32_t(level.mask.size())));
            }
            // Retain compact hit masks, not decoded RGBA copies per frame/variant.
            for (const auto &[frameName, candidate] : atlas.frames)
            {
                if (candidate.page != frame.page)
                {
                    continue;
                }
                const std::array<int, 4> &rect = candidate.rectangle;
                page.opacity[frameName].assignFromBgraRegion(
                    base.pixels, base.width, base.height, rect[0], rect[1], rect[2], rect[3]);
            }
        }
        if (!bgfx::isValid(m_maskSampler))
        {
            m_maskSampler = bgfx::createUniform("s_spriteMask", bgfx::UniformType::Sampler);
            m_lookupSampler = bgfx::createUniform("s_spriteLookup", bgfx::UniformType::Sampler);
            m_rectUniform = bgfx::createUniform("u_spriteAtlasRect", bgfx::UniformType::Vec4);
            m_texelUniform = bgfx::createUniform("u_spriteAtlasTexel", bgfx::UniformType::Vec4);
            m_chromaUniform = bgfx::createUniform("u_spriteChroma", bgfx::UniformType::Vec4);
            m_secondChromaUniform = bgfx::createUniform("u_spriteSecondChroma", bgfx::UniformType::Vec4);
            m_thirdChromaUniform = bgfx::createUniform("u_spriteThirdChroma", bgfx::UniformType::Vec4);
            m_fourthChromaUniform = bgfx::createUniform("u_spriteFourthChroma", bgfx::UniformType::Vec4);
        }
        const std::array<int, 4> &rect = frame.rectangle;
        const float tier = atlas.pixelsPerLogicalPixel;
        texture.textureName = name;
        texture.paletteId = variant;
        texture.width = float(rect[2]) / tier;
        texture.height = float(rect[3]) / tier;
        texture.physicalWidth = rect[2];
        texture.physicalHeight = rect[3];
        texture.offsetX = (float(frame.cropOrigin[0]) + float(rect[2]) * 0.5f) / tier - atlas.logicalPivot[0];
        texture.offsetY = float(atlas.logicalCanvas[1]) - float(frame.cropOrigin[1] + rect[3]) / tier;
        const std::array<int, 4> &gpuRect = page.rectangles.at(reference->frame);
        texture.atlasRect = {float(gpuRect[0]) / page.size[0], float(gpuRect[1]) / page.size[1],
            float(gpuRect[2]) / page.size[0], float(gpuRect[3]) / page.size[1]};
        texture.atlasTexel = {1.0f / page.size[0], 1.0f / page.size[1], float(SpriteAtlasMaxMip), 0};
        texture.chroma = atlas.variants.at(variant).chroma;
        texture.secondChroma = atlas.variants.at(variant).secondChroma;
        texture.thirdChroma = atlas.variants.at(variant).thirdChroma;
        texture.fourthChroma = atlas.variants.at(variant).fourthChroma;
        texture.textureHandle = page.base;
        texture.maskHandle = page.mask;
        texture.lookupHandle = appearance.lookup.empty() ? page.mask : package.lookups.at(variant);
        texture.opacityMask = page.opacity.at(reference->frame);
        texture.atlas = true;
        return true;
    }
    catch (const std::exception &exception)
    {
        m_failed.insert(key);
        std::cerr << "[SpriteAtlas] " << key << ": " << exception.what() << '\n';
        return false;
    }
}

void SpriteAtlasCache::preload(
    const Engine::AssetFileSystem &assets, const SpriteFrameTable &frames, uint16_t spriteId)
{
    if (spriteId == 0)
    {
        return;
    }
    for (size_t index = spriteId; index <= std::numeric_limits<uint16_t>::max(); ++index)
    {
        const SpriteFrameEntry *pFrame = frames.getFrame(uint16_t(index), 0);
        if (pFrame == nullptr)
        {
            break;
        }
        for (int octant = 0; octant < 8; ++octant)
        {
            const std::string name = SpriteFrameTable::resolveTexture(*pFrame, octant).textureName;
            const std::optional<Engine::SpriteAtlasReference> reference = Engine::parseSpriteAtlasReference(name);
            if (!reference)
            {
                continue;
            }
            const auto existing = m_packages.find(reference->package);
            if (existing != m_packages.end() && existing->second.preloaded)
            {
                continue;
            }
            SpriteBillboardTexture texture;
            if (!load(assets, name, pFrame->paletteId, texture))
            {
                continue;
            }
            Package &package = m_packages.at(reference->package);
            std::unordered_set<int> attemptedPages;
            for (const auto &[frameName, frame] : package.atlas.frames)
            {
                if (!bgfx::isValid(package.pages[frame.page].base) && attemptedPages.insert(frame.page).second)
                {
                    load(assets, "atlas:" + reference->package + "/" + frameName, pFrame->paletteId, texture);
                }
            }
            package.preloaded = true;
        }
        if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
        {
            break;
        }
    }
}

bgfx::ProgramHandle SpriteAtlasCache::bind(
    const SpriteBillboardTexture &texture, bgfx::ProgramHandle nativeProgram) const
{
    if (!texture.atlas)
    {
        return nativeProgram;
    }
    bindTexture(1, m_maskSampler, texture.maskHandle, TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setTexture(2, m_lookupSampler, texture.lookupHandle,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT
            | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT);
    bgfx::setUniform(m_rectUniform, texture.atlasRect.data());
    std::array<float, 4> texel = texture.atlasTexel;
    if (!textureFilteringEnabled())
    {
        texel[2] = 0;
    }
    bgfx::setUniform(m_texelUniform, texel.data());
    bgfx::setUniform(m_chromaUniform, texture.chroma.data());
    bgfx::setUniform(m_secondChromaUniform, texture.secondChroma.data());
    bgfx::setUniform(m_thirdChromaUniform, texture.thirdChroma.data());
    bgfx::setUniform(m_fourthChromaUniform, texture.fourthChroma.data());
    return m_program;
}

void SpriteAtlasCache::clear(bool destroyGpu)
{
    if (destroyGpu)
    {
        for (auto &[name, package] : m_packages)
        {
            for (const auto &[variant, lookup] : package.lookups)
            {
                bgfx::destroy(lookup);
            }
            for (Page &page : package.pages)
            {
                if (bgfx::isValid(page.base))
                {
                    bgfx::destroy(page.base);
                }
                if (bgfx::isValid(page.mask))
                {
                    bgfx::destroy(page.mask);
                }
            }
        }
        for (bgfx::UniformHandle uniform : {
            m_maskSampler, m_lookupSampler, m_rectUniform, m_texelUniform, m_chromaUniform, m_secondChromaUniform,
            m_thirdChromaUniform, m_fourthChromaUniform})
        {
            if (bgfx::isValid(uniform))
            {
                bgfx::destroy(uniform);
            }
        }
        if (bgfx::isValid(m_program))
        {
            bgfx::destroy(m_program);
        }
    }
    m_packages.clear();
    m_failed.clear();
    m_program = BGFX_INVALID_HANDLE;
    m_maskSampler = BGFX_INVALID_HANDLE;
    m_lookupSampler = BGFX_INVALID_HANDLE;
    m_rectUniform = BGFX_INVALID_HANDLE;
    m_texelUniform = BGFX_INVALID_HANDLE;
    m_chromaUniform = BGFX_INVALID_HANDLE;
    m_secondChromaUniform = BGFX_INVALID_HANDLE;
    m_thirdChromaUniform = BGFX_INVALID_HANDLE;
    m_fourthChromaUniform = BGFX_INVALID_HANDLE;
}
}
