#include "game/render/SpriteAtlasCache.h"

#include "engine/ImageAssetLoader.h"
#include "game/render/TextureFiltering.h"
#include "game/render/SpriteAtlasMipmaps.h"
#include "game/tables/SpriteTables.h"

#include <iostream>
#include <chrono>
#include <deque>
#include <future>
#include <thread>
#include <cmath>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>

namespace OpenYAMM::Game
{
SpriteAtlasCache::Statistics SpriteAtlasCache::statistics() const
{
    Statistics result = m_statistics;
    result.residentBytes = m_residentBytes;
    for (const auto &[name, package] : m_packages)
    {
        for (const Page &page : package.pages)
        {
            result.residentPages += bgfx::isValid(page.base);
        }
    }
    return result;
}

void SpriteAtlasCache::beginLevel(const Engine::AssetFileSystem &assets, std::function<void()> progress)
{
    if (m_generation != assets.contentGeneration())
    {
        for (auto &[name, package] : m_packages)
        {
            releasePackage(package, true);
        }
        m_packages.clear();
        m_failed.clear();
        m_generation = assets.contentGeneration();
    }
    ++m_level;
    m_statistics = {};
    m_progress = std::move(progress);
}

void SpriteAtlasCache::releasePackage(Package &package, bool destroyGpu)
{
    if (destroyGpu)
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
    m_residentBytes -= package.gpuBytes;
}

void SpriteAtlasCache::trim(size_t incomingBytes)
{
#if defined(__ANDROID__)
    constexpr size_t budget = 256 * 1024 * 1024;
#else
    constexpr size_t budget = 768 * 1024 * 1024;
#endif
    while (m_residentBytes + incomingBytes > budget)
    {
        auto oldest = m_packages.end();
        for (auto entry = m_packages.begin(); entry != m_packages.end(); ++entry)
        {
            if (entry->second.lastUse != m_level
                && (oldest == m_packages.end() || entry->second.lastUse < oldest->second.lastUse))
            {
                oldest = entry;
            }
        }
        if (oldest == m_packages.end())
        {
            break; // The active map's required resources stay pinned even if it exceeds the retention budget.
        }
        releasePackage(oldest->second, true);
        m_packages.erase(oldest);
    }
}

void SpriteAtlasCache::setProgram(bgfx::ProgramHandle program)
{
    m_program = program;
}

void SpriteAtlasCache::setOutlineProgram(bgfx::ProgramHandle program)
{
    m_outlineProgram = program;
    m_outlineSampler = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
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
        Package &package = findPackage(assets, reference->package);
        const std::string &root = package.root;
        const Engine::SpriteAtlas &atlas = package.atlas;
        if (!atlas.frames.contains(reference->frame) || !atlas.variants.contains(variant))
        {
            throw std::runtime_error("Atlas frame or variant is not declared");
        }
        const Engine::SpriteAtlasFrame &frame = atlas.frames.at(reference->frame);
        const int appearanceId = frame.paletteOverrides.contains(variant) ? frame.paletteOverrides.at(variant) : variant;
        const Engine::SpriteAtlasVariant &appearance = atlas.variants.at(appearanceId);
        if (!appearance.lookup.empty() && !package.lookups.contains(appearanceId))
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
            package.lookups.emplace(appearanceId, lookup);
            package.gpuBytes += expected;
            m_residentBytes += expected;
        }
        Page &page = package.pages[frame.page];
        if (!bgfx::isValid(page.base))
        {
            publishPage(package, frame.page, preparePage(assets, package, frame.page,
                bgfx::getCaps()->limits.maxTextureSize));
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
        texture.width = frame.drawSize[0] / tier;
        texture.height = frame.drawSize[1] / tier;
        texture.canvasWidth = float(atlas.logicalCanvas[0]);
        texture.canvasHeight = float(atlas.logicalCanvas[1]);
        texture.physicalWidth = rect[2];
        texture.physicalHeight = rect[3];
        texture.offsetX = (frame.cropOrigin[0] + frame.drawSize[0] * 0.5f) / tier - atlas.logicalPivot[0];
        texture.offsetY = float(atlas.logicalCanvas[1]) - (frame.cropOrigin[1] + frame.drawSize[1]) / tier;
        const std::array<int, 4> &gpuRect = page.rectangles.at(reference->frame);
        texture.atlasRect = {float(gpuRect[0]) / page.size[0], float(gpuRect[1]) / page.size[1],
            float(gpuRect[2]) / page.size[0], float(gpuRect[3]) / page.size[1]};
        texture.atlasTexel = {1.0f / page.size[0], 1.0f / page.size[1], float(SpriteAtlasMaxMip), atlas.brightnessMultiplier};
        texture.chroma = appearance.chroma;
        texture.secondChroma = appearance.secondChroma;
        texture.thirdChroma = appearance.thirdChroma;
        texture.fourthChroma = appearance.fourthChroma;
        texture.textureHandle = page.base;
        texture.maskHandle = page.mask;
        texture.lookupHandle = appearance.lookup.empty() ? page.mask : package.lookups.at(appearanceId);
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

SpriteAtlasCache::Package &SpriteAtlasCache::findPackage(
    const Engine::AssetFileSystem &assets, const std::string &name)
{
    auto existing = m_packages.find(name);
    if (existing == m_packages.end())
    {
        Package package;
        package.root = "engine/sprites_new/" + name + "/";
        const std::optional<std::string> text = assets.readTextFile(package.root + "manifest.json");
        std::string error;
        const std::optional<Engine::SpriteAtlas> atlas = text ? Engine::SpriteAtlas::parse(*text, error) : std::nullopt;
        if (!atlas || atlas->schemaVersion != SpriteAtlasCookVersion)
        {
            throw std::runtime_error("Cannot load " + package.root
                + "manifest.json (requires cooked schema 2): " + error);
        }
        package.manifestHash = spriteAtlasContentHash(
            std::span(reinterpret_cast<const uint8_t *>(text->data()), text->size()));
        package.atlas = *atlas;
        package.pages.resize(atlas->pages.size());
        existing = m_packages.emplace(name, std::move(package)).first;
    }
    existing->second.lastUse = m_level;
    return existing->second;
}

PreparedSpriteAtlasPage SpriteAtlasCache::preparePage(const Engine::AssetFileSystem &assets,
    const Package &package, int index, int maxTextureSize) const
{
    const Engine::SpriteAtlasPage &description = package.atlas.pages.at(index);
    const std::string path = package.root + description.texture;
    const std::optional<Engine::AssetFileInfo> cooked = assets.fileInfo(path);
    if (!cooked || cooked->size > SpriteAtlasCookByteLimit)
    {
        throw std::runtime_error("Missing/invalid " + path + "; build openyamm_cook_sprite_atlases");
    }
    const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(path);
    if (!bytes)
    {
        throw std::runtime_error("Cannot read " + path);
    }
    return decodeCookedSpriteAtlasPage(*bytes, package.atlas, index,
        package.manifestHash, maxTextureSize);
}

void SpriteAtlasCache::publishPage(Package &package, int index, PreparedSpriteAtlasPage prepared)
{
    Page &page = package.pages.at(index);
    const bgfx::TextureFormat::Enum baseFormat = Engine::textureBlockFormat(prepared.baseCodec);
    const bgfx::TextureFormat::Enum maskFormat = Engine::textureBlockFormat(prepared.maskCodec);
    for (bgfx::TextureFormat::Enum format : {baseFormat, maskFormat})
    {
        const uint32_t caps = bgfx::getCaps()->formats[format];
        if (!(caps & BGFX_CAPS_FORMAT_TEXTURE_2D) || (caps & BGFX_CAPS_FORMAT_TEXTURE_2D_EMULATED))
        {
            throw std::runtime_error("GPU cannot sample this sprite texture profile natively: "
                + package.atlas.textureProfile);
        }
    }
    page.size = {prepared.levels.front().width, prepared.levels.front().height};
    // bgfx allocates the full mip chain; include its small unsampled tail in the cache budget.
    bgfx::TextureInfo baseInfo;
    bgfx::TextureInfo maskInfo;
    bgfx::calcTextureSize(baseInfo, uint16_t(page.size[0]), uint16_t(page.size[1]), 1, false, true, 1, baseFormat);
    bgfx::calcTextureSize(maskInfo, uint16_t(page.size[0]), uint16_t(page.size[1]), 1, false, true, 1, maskFormat);
    const size_t gpuBytes = size_t(baseInfo.storageSize) + maskInfo.storageSize;
    trim(gpuBytes);
    page.base = bgfx::createTexture2D(uint16_t(page.size[0]), uint16_t(page.size[1]), true, 1,
        baseFormat, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    page.mask = bgfx::createTexture2D(uint16_t(page.size[0]), uint16_t(page.size[1]), true, 1,
        maskFormat, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
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
        throw std::runtime_error("Unable to allocate atlas textures");
    }
    for (uint8_t mip = 0; mip < prepared.levels.size(); ++mip)
    {
        const SpriteAtlasTextureLevel &level = prepared.levels[mip];
        bgfx::updateTexture2D(page.base, 0, mip, 0, 0, uint16_t(level.width), uint16_t(level.height),
            bgfx::copy(level.baseBlocks.data(), uint32_t(level.baseBlocks.size())));
        bgfx::updateTexture2D(page.mask, 0, mip, 0, 0, uint16_t(level.width), uint16_t(level.height),
            bgfx::copy(level.maskBlocks.data(), uint32_t(level.maskBlocks.size())));
    }
    page.rectangles = std::move(prepared.rectangles);
    page.opacity = std::move(prepared.opacity);
    package.gpuBytes += gpuBytes;
    m_residentBytes += gpuBytes;
    ++m_statistics.uploadedPages;
    if (m_progress)
    {
        m_progress();
    }
}

void SpriteAtlasCache::preloadPackage(const Engine::AssetFileSystem &assets, const std::string &name)
{
    if (m_failed.contains(name))
    {
        return;
    }
    try
    {
        const std::optional<Engine::SpriteAtlasReference> reference = Engine::parseSpriteAtlasReference(name);
        if (!reference || !hasProgram())
        {
            return;
        }
        Package &package = findPackage(assets, reference->package);
        if (package.preloaded)
        {
            return;
        }
        struct Pending
        {
            int index;
            size_t bytes;
            std::future<PreparedSpriteAtlasPage> future;
        };
        std::deque<Pending> pending;
        const size_t workers = std::clamp(size_t(std::thread::hardware_concurrency() / 2), size_t(1), size_t(2));
        constexpr size_t byteBudget = 256 * 1024 * 1024;
        size_t pendingBytes = 0;
        size_t next = 0;
        const int maxTextureSize = bgfx::getCaps()->limits.maxTextureSize;
        while (next < package.pages.size() || !pending.empty())
        {
            while (next < package.pages.size() && pending.size() < workers)
            {
                if (bgfx::isValid(package.pages[next].base))
                {
                    ++next;
                    continue;
                }
                const std::string path = package.root + package.atlas.pages[next].texture;
                std::unique_ptr<Engine::AssetReadStream> stream = assets.openReadStream(path);
                std::array<uint8_t, SpriteAtlasCookHeaderBytes> header;
                if (!stream || stream->length() < 0
                    || stream->read(header.data(), header.size()) != int64_t(header.size()))
                {
                    throw std::runtime_error("Missing/truncated " + path);
                }
                const size_t bytes = cookedSpriteAtlasPreparationBytes(header, size_t(stream->length()));
                if (!pending.empty() && pendingBytes + bytes > byteBudget)
                {
                    break;
                }
                const int index = int(next++);
                pending.push_back({index, bytes, std::async(std::launch::async,
                    [this, &assets, &package, index, maxTextureSize]()
                    {
                        return preparePage(assets, package, index, maxTextureSize);
                    })});
                pendingBytes += bytes;
                m_statistics.peakPreparationBytes = std::max(m_statistics.peakPreparationBytes, pendingBytes);
                m_statistics.peakPreparationJobs = std::max(m_statistics.peakPreparationJobs, pending.size());
            }
            if (pending.empty())
            {
                continue;
            }
            Pending &job = pending.front();
            while (job.future.wait_for(std::chrono::milliseconds(1)) != std::future_status::ready)
            {
                if (m_progress)
                {
                    m_progress();
                }
            }
            publishPage(package, job.index, job.future.get());
            pendingBytes -= job.bytes;
            pending.pop_front();
        }
        SpriteBillboardTexture texture;
        // Variant lookups are small and must not first appear during combat or an animation change.
        for (const auto &[id, appearance] : package.atlas.variants)
        {
            load(assets, name, int16_t(id), texture);
        }
        package.preloaded = true;
    }
    catch (const std::exception &exception)
    {
        m_failed.insert(name);
        std::cerr << "[SpriteAtlas] " << name << ": " << exception.what() << '\n';
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
            if (Engine::parseSpriteAtlasReference(name))
            {
                preloadPackage(assets, name);
            }
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

bgfx::ProgramHandle SpriteAtlasCache::bindOutline(
    const SpriteBillboardTexture &texture, bgfx::ProgramHandle nativeProgram) const
{
    if (!texture.atlas)
    {
        return nativeProgram;
    }
    // Linear alpha sampling smooths the contour independently of the art filtering preference.
    bgfx::setTexture(0, m_outlineSampler, texture.textureHandle, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setUniform(m_rectUniform, texture.atlasRect.data());
    bgfx::setUniform(m_texelUniform, texture.atlasTexel.data());
    return m_outlineProgram;
}

void SpriteAtlasCache::clear(bool destroyGpu)
{
    for (auto &[name, package] : m_packages)
    {
        releasePackage(package, destroyGpu);
    }

    if (destroyGpu)
    {
        for (bgfx::UniformHandle uniform : {
            m_maskSampler, m_lookupSampler, m_rectUniform, m_texelUniform, m_chromaUniform, m_secondChromaUniform,
            m_thirdChromaUniform, m_fourthChromaUniform, m_outlineSampler})
        {
            if (bgfx::isValid(uniform))
            {
                bgfx::destroy(uniform);
            }
        }
        if (bgfx::isValid(m_outlineProgram))
        {
            bgfx::destroy(m_outlineProgram);
        }
        if (bgfx::isValid(m_program))
        {
            bgfx::destroy(m_program);
        }
    }
    m_packages.clear();
    m_failed.clear();
    m_progress = {};
    m_program = BGFX_INVALID_HANDLE;
    m_outlineProgram = BGFX_INVALID_HANDLE;
    m_outlineSampler = BGFX_INVALID_HANDLE;
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
