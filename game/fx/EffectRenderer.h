#pragma once

#include "engine/ImageAssetLoader.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstddef>
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace bx
{
struct Vec3;
}

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class EffectResourceLibrary;
class EffectSystem;
struct EffectSpriteResource;
class WorldFxRenderResources;

class EffectRenderer
{
public:
    struct Diagnostics
    {
        size_t sourceParticles = 0;
        size_t sourceFixedSprites = 0;
        size_t visibleRibbons = 0;
        size_t visibleQuads = 0;
        size_t drawCalls = 0;
        size_t textureSwitches = 0;
        size_t loadedTextures = 0;
        size_t estimatedTextureBytes = 0;
        double worldQuadArea = 0.0;
    };

    struct Texture
    {
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
        int width = 0;
        int height = 0;
    };

    void render(
        WorldFxRenderResources &resources,
        const EffectSystem &effects,
        const EffectResourceLibrary &effectResources,
        const Engine::AssetFileSystem &assetFileSystem,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
    void shutdown(bool destroyGpu);
    // Loads the textures of the active effects' sprites and of extraSpriteResources (effects that may start later,
    // such as projectile flights and impacts), so their first use does not stall on image decoding.
    void preload(const EffectSystem &effects, const EffectResourceLibrary &effectResources,
        const Engine::AssetFileSystem &assetFileSystem, const std::vector<std::string> &extraSpriteResources = {});
    // Uses the other renderer's texture cache from now on, so the indoor and outdoor renderers load each effect
    // texture once between them.
    void shareTextureCache(const EffectRenderer &other);
    const Diagnostics &diagnostics() const;

private:
    // An effect sprite's frames packed into one texture, so particles at different animation frames still draw in
    // one batch; a single-frame sprite uses its own texture whole.
    struct SpriteAtlas
    {
        const Texture *pTexture = nullptr;
        // Per frame: u0, v0, u1, v1.
        std::vector<std::array<float, 4>> frameUvs;
        uint32_t framesPerSecond = 0;
        float logicalWidth = 0.0f;
        float logicalHeight = 0.0f;
    };

    struct StringHash
    {
        using is_transparent = void;
        size_t operator()(std::string_view value) const
        {
            return std::hash<std::string_view>{}(value);
        }
    };

    struct TextureCache
    {
        std::unordered_map<std::string, Texture> textures;
        std::unordered_map<std::string, SpriteAtlas, StringHash, std::equal_to<>> atlases;
        Engine::BinaryAssetCache binaryAssets;
    };

    const Texture *loadTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &path);
    // A sprite read, decoded, packed and edge-bled without bgfx (safe on any thread); finishAtlas uploads it.
    // rawTexels keeps the texels as stored, without the transparent-edge bleed, for additive light that ignores the
    // texture's alpha (EffectSpriteDefinition::additiveTextureAlpha); it is cached apart from the bled atlas.
    struct PreparedAtlas;
    static PreparedAtlas prepareAtlas(
        const EffectResourceLibrary &effectResources,
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &spriteResource,
        bool rawTexels = false);
    const SpriteAtlas *finishAtlas(PreparedAtlas &prepared);
    const SpriteAtlas *loadAtlas(
        const EffectResourceLibrary &effectResources,
        const Engine::AssetFileSystem &assetFileSystem,
        std::string_view spriteResource,
        bool rawTexels);
    void renderRibbons(
        WorldFxRenderResources &resources,
        const EffectSystem &effects,
        const EffectResourceLibrary &effectResources,
        const Engine::AssetFileSystem &assetFileSystem,
        uint16_t viewId,
        const bx::Vec3 &cameraPosition,
        const bx::Vec3 &cameraForward);
    bool initializeRibbonProgram();

    bgfx::ProgramHandle m_ribbonProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_ribbonParamsUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_ribbonScrollUniform = BGFX_INVALID_HANDLE;
    bgfx::VertexLayout m_ribbonLayout;
    bool m_ribbonProgramAttempted = false;

    std::shared_ptr<TextureCache> m_pTextureCache = std::make_shared<TextureCache>();
    Diagnostics m_diagnostics;
};
}
