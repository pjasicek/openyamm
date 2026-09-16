#pragma once

#include "engine/AssetFileSystem.h"
#include "engine/SpriteAtlas.h"
#include "game/render/BillboardOpacityMask.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <map>
#include <unordered_set>

namespace OpenYAMM::Game
{
class SpriteFrameTable;

struct SpriteBillboardTexture
{
    std::string textureName;
    int16_t paletteId = 0;
    float width = 0;
    float height = 0;
    int physicalWidth = 0;
    int physicalHeight = 0;
    BillboardOpacityMask opacityMask;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle maskHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle lookupHandle = BGFX_INVALID_HANDLE;
    std::array<float, 4> atlasRect = {};
    std::array<float, 4> atlasTexel = {};
    std::array<float, 4> chroma = {};
    std::array<float, 4> secondChroma = {};
    std::array<float, 4> thirdChroma = {};
    std::array<float, 4> fourthChroma = {};
    float offsetX = 0;
    float offsetY = 0;
    bool atlas = false;
};

// Coordinates relative to the existing actor's native bottom-anchored logical canvas.
inline bx::Vec3 spriteBillboardCenter(
    float x, float y, float z, const bx::Vec3 &cameraRight, const bx::Vec3 &cameraUp,
    const SpriteBillboardTexture &texture, float scale, bool mirrored)
{
    const float horizontal = texture.offsetX * scale * (mirrored ? -1.0f : 1.0f);
    const float vertical = (texture.height * 0.5f + texture.offsetY) * scale;
    return {x + cameraRight.x * horizontal + cameraUp.x * vertical,
        y + cameraRight.y * horizontal + cameraUp.y * vertical,
        z + cameraRight.z * horizontal + cameraUp.z * vertical};
}

class SpriteAtlasCache
{
public:
    void setProgram(bgfx::ProgramHandle program);
    bool load(const Engine::AssetFileSystem &assets, const std::string &name, int16_t variant,
        SpriteBillboardTexture &texture);
    // Warm every page of packages referenced by this animation during map loading.
    void preload(const Engine::AssetFileSystem &assets, const SpriteFrameTable &frames, uint16_t spriteId);
    bgfx::ProgramHandle bind(const SpriteBillboardTexture &texture, bgfx::ProgramHandle nativeProgram) const;
    void clear(bool destroyGpu);

private:
    struct Page
    {
        bgfx::TextureHandle base = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle mask = BGFX_INVALID_HANDLE;
        std::unordered_map<std::string, BillboardOpacityMask> opacity;
        std::unordered_map<std::string, std::array<int, 4>> rectangles;
        std::array<int, 2> size = {};
    };
    struct Package
    {
        Engine::SpriteAtlas atlas;
        std::vector<Page> pages;
        std::map<int, bgfx::TextureHandle> lookups;
        bool preloaded = false;
    };
    std::map<std::string, Package> m_packages;
    std::unordered_set<std::string> m_failed;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_maskSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lookupSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_rectUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_texelUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_chromaUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_secondChromaUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_thirdChromaUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fourthChromaUniform = BGFX_INVALID_HANDLE;
};
}
