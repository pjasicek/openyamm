#pragma once

#include "engine/AssetFileSystem.h"
#include "game/render/TextureFiltering.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/UiLayoutManager.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct GameplayAssetLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> assetPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
};

struct GameplayHudTextureData
{
    std::string textureName;
    int width = 0;
    int height = 0;
    int physicalWidth = 0;
    int physicalHeight = 0;
    std::vector<uint8_t> bgraPixels;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayHudFontGlyphMetricsData
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
};

struct GameplayHudFontData
{
    std::string fontName;
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    int atlasCellWidth = 0;
    int atlasWidth = 0;
    int atlasHeight = 0;
    std::array<GameplayHudFontGlyphMetricsData, 256> glyphMetrics = {{}};
    std::vector<uint8_t> mainAtlasPixels;
    bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayHudFontColorTextureData
{
    std::string fontName;
    uint32_t colorAbgr = 0xffffffffu;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayHudTextureColorTextureData
{
    std::string textureName;
    uint32_t colorAbgr = 0xffffffffu;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayUiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

class GameplayHudCommon
{
public:
    using SubmitTexturedQuadFn = std::function<void(
        bgfx::TextureHandle,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        TextureFilterProfile)>;
    using FindHudFontFn = std::function<const GameplayHudFontData *(const std::string &)>;
    using EnsureHudFontColorFn = std::function<bgfx::TextureHandle(const GameplayHudFontData &, uint32_t)>;
    using RenderHudFontLayerFn = std::function<void(
        const GameplayHudFontData &,
        bgfx::TextureHandle,
        const std::string &,
        float,
        float,
        float)>;

    static GameplayUiViewportRect computeUiViewportRect(int screenWidth, int screenHeight);
    static GameplayUiViewportRect computeAnchorRect(
        UiLayoutManager::LayoutAnchorSpace anchorSpace,
        int screenWidth,
        int screenHeight);
    static float snappedHudFontScale(float scale);
    static GameplayResolvedHudLayoutElement resolveAttachedHudLayoutRect(
        UiLayoutManager::LayoutAttachMode attachTo,
        const GameplayResolvedHudLayoutElement &parent,
        float width,
        float height,
        float gapX,
        float gapY,
        float scale);
    static std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const UiLayoutManager &layoutManager,
        const std::unordered_map<std::string, float> &runtimeHeightOverrides,
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight);
    static bool isPointerInsideResolvedElement(
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY);
    static const std::string *resolveInteractiveAssetName(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed);

    static std::optional<std::string> findCachedAssetPath(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &directoryPath,
        const std::string &fileName);
    static std::optional<std::vector<uint8_t>> readCachedBinaryFile(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &assetPath);
    static std::optional<std::array<uint8_t, 256 * 3>> loadCachedActPalette(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        int16_t paletteId);
    static std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &textureName,
        int &width,
        int &height);
    static const GameplayHudTextureData *findHudTexture(
        const std::vector<GameplayHudTextureData> &textures,
        const std::unordered_map<std::string, size_t> &textureIndexByName,
        const std::string &textureName);
    static bool loadHudTexture(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &textureName,
        std::vector<GameplayHudTextureData> &textures,
        std::unordered_map<std::string, size_t> &textureIndexByName);
    static std::optional<GameplayHudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels,
        std::vector<GameplayHudTextureData> &textures,
        std::unordered_map<std::string, size_t> &textureIndexByName);
    static const GameplayHudFontData *findHudFont(
        const std::vector<GameplayHudFontData> &fonts,
        const std::string &fontName);
    static bool loadHudFont(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &fontName,
        std::vector<GameplayHudFontData> &fonts);
    static bool tryGetOpaqueHudTextureBounds(
        const GameplayHudTextureData &texture,
        Engine::AssetScaleTier assetScaleTier,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY);
    static bgfx::TextureHandle ensureHudTextureColor(
        const GameplayHudTextureData &texture,
        uint32_t colorAbgr,
        std::vector<GameplayHudTextureColorTextureData> &colorTextures);
    static bgfx::TextureHandle ensureHudFontMainTextureColor(
        const GameplayHudFontData &font,
        uint32_t colorAbgr,
        std::vector<GameplayHudFontColorTextureData> &colorTextures);
    static float measureHudTextWidth(const GameplayHudFontData &font, const std::string &text);
    static std::string clampHudTextToWidth(const GameplayHudFontData &font, const std::string &text, float maxWidth);
    static std::vector<std::string> wrapHudTextToWidth(
        const GameplayHudFontData &font,
        const std::string &text,
        float maxWidth);
    static void renderHudFontLayer(
        const GameplayHudFontData &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale,
        const SubmitTexturedQuadFn &submitTexturedQuad);
    static void renderLayoutLabel(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        const std::string &label,
        const FindHudFontFn &findHudFont,
        const EnsureHudFontColorFn &ensureHudFontColor,
        const RenderHudFontLayerFn &renderHudFontLayer);
};
} // namespace OpenYAMM::Game
