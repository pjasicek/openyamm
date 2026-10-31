#pragma once

#include "engine/AssetFileSystem.h"
#include "engine/FontAsset.h"
#include "engine/render/CookedTexture.h"
#include "game/render/TextureFiltering.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/UiLayoutManager.h"

#include <bgfx/bgfx.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct GameplayActorInspectClock
{
    uint32_t ticks = 1;
    uint32_t lastUpdateTicks = 0;
    bool wasVisible = false;

    uint32_t update(bool visible, uint32_t nowTicks)
    {
        if (visible && wasVisible)
        {
            ticks += std::min(nowTicks - lastUpdateTicks, 32u);
        }
        wasVisible = visible;
        lastUpdateTicks = nowTicks;
        return ticks;
    }
};

struct GameplayAssetLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> assetPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<std::string, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesByKey;
};

struct GameplayHudTextureData
{
    std::string textureName;
    int width = 0;
    int height = 0;
    int physicalWidth = 0;
    int physicalHeight = 0;
    Engine::AssetScaleTier assetScaleTier = Engine::AssetScaleTier::X1;
    // Read through GameplayHudCommon::hudTexturePixels: cooked art leaves it empty until a CPU use decodes it.
    mutable std::vector<uint8_t> bgraPixels;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    // Cooked art (tools/cook_ui_textures.py) is padded to whole 4x4 blocks: draws scale UVs by these.
    float uScale = 1.0f;
    float vScale = 1.0f;
    // The cooked texture and this texture's block-aligned cell in it. A face set atlas stays in memory (portrait
    // tints read its frames); a single image is read again from cookedPath on its first CPU use.
    std::shared_ptr<const Engine::CookedTexture> cookedSource;
    std::string cookedPath;
    const Engine::AssetFileSystem *pCookedAssetFileSystem = nullptr;
    int cookedCellX = 0;
    int cookedCellY = 0;
    int cookedCellWidth = 0;
    int cookedCellHeight = 0;
};

using GameplayHudFontGlyphMetricsData = Engine::FontGlyphMetrics;

struct GameplayHudFontData : Engine::FontAtlas
{
    bool smooth = false;
    std::string fontName;
    // 0: the face's layout size; otherwise the display height an independent outline face was rasterized at.
    int rasterPixelHeight = 0;
    bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
    // The main atlas with white glyphs, tinted at draw time; the main atlas itself when its glyphs are white.
    bgfx::TextureHandle tintTextureHandle = BGFX_INVALID_HANDLE;
};

enum class GameplayHudTextureColorMode
{
    Solid,
    Modulated,
};

struct GameplayHudTextureColorTextureData
{
    std::string textureName;
    uint32_t colorAbgr = 0xffffffffu;
    GameplayHudTextureColorMode colorMode = GameplayHudTextureColorMode::Solid;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
};

enum class GameplayHudBitmapTransparencyMode
{
    HudColorKey,
    ItemIcon
};

struct GameplayUiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

// The font atlases the gameplay HUD and the menus draw with. Each face, and each raster height of an independent
// outline face, is rasterized, mip-filtered and uploaded once (several at a time on the load workers) and kept for the
// rest of the run: fonts are engine assets, the same for every map and world. Its handles stay valid until release().
class SharedFontCache
{
public:
    struct Request
    {
        std::string fontName;
        // 0: the face's layout size; otherwise the display height to rasterize an independent outline face at.
        int pixelHeight = 0;
    };

    // Loads the requested faces that are not cached yet. A face that fails is reported once and not retried.
    static void ensure(const Engine::AssetFileSystem &assetFileSystem, const std::vector<Request> &requests);
    static const GameplayHudFontData *find(const std::string &fontName, int pixelHeight = 0);
    // Drops the extra raster heights; menus request the ones a new window size needs again.
    static void releaseRasterSizes();
    // At shutdown, with destroyGpu false once the bgfx context is gone.
    static void release(bool destroyGpu);
};

class GameplayHudCommon
{
public:
    // Shared logical viewport for portrait rendering and pointer hit tests.
    static constexpr float PartyPortraitNativeWidth = 60.0f;
    static constexpr float PartyPortraitNativeHeight = 80.0f;

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
        TextureFilterProfile,
        uint32_t)>;
    using FindHudFontFn = std::function<const GameplayHudFontData *(const std::string &)>;
    using RenderHudFontLayerFn = std::function<void(
        const GameplayHudFontData &,
        const GameplayHudFontLayer &,
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
    static float touchPanelVerticalOffset(
        const GameplayResolvedHudLayoutElement &panel, const GameplayResolvedHudLayoutElement &basebar)
    {
        const float ornamentMargin = 22.0f * basebar.scale;
        if (panel.x + panel.width <= basebar.x - ornamentMargin
            || panel.x >= basebar.x + basebar.width + ornamentMargin)
        {
            return 0.0f;
        }
        return std::min(0.0f, basebar.y - 12.0f * panel.scale - panel.y - panel.height);
    }
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
        const std::unordered_map<std::string, float> &runtimeWidthOverrides,
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
        int16_t paletteId,
        const std::string &worldId = {});
    static std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &textureName,
        int &width,
        int &height,
        GameplayHudBitmapTransparencyMode transparencyMode = GameplayHudBitmapTransparencyMode::HudColorKey,
        Engine::AssetScaleTier *pLoadedTier = nullptr);
    static std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height,
        const std::string &worldId = {},
        Engine::AssetScaleTier *pLoadedTier = nullptr);
    static const GameplayHudTextureData *findHudTexture(
        const std::vector<GameplayHudTextureData> &textures,
        const std::unordered_map<std::string, size_t> &textureIndexByName,
        const std::string &textureName);
    static bool loadHudTexture(
        const Engine::AssetFileSystem *pAssetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &textureName,
        std::vector<GameplayHudTextureData> &textures,
        std::unordered_map<std::string, size_t> &textureIndexByName,
        GameplayHudBitmapTransparencyMode transparencyMode = GameplayHudBitmapTransparencyMode::HudColorKey);
    // The texture's BGRA pixels at its physical size; cooked art decodes its blocks on the first call.
    static const std::vector<uint8_t> &hudTexturePixels(const GameplayHudTextureData &texture);
    // The cooked portrait set holding a frame (all its frames load at once), and a cooked single image. False when the
    // art has no cooked file in the active scale tier; throws on a corrupt or mismatched cooked file.
    static bool loadCookedFaceSet(
        const Engine::AssetFileSystem &assetFileSystem,
        GameplayAssetLoadCache &cache,
        const std::string &normalizedName,
        std::vector<GameplayHudTextureData> &textures,
        std::unordered_map<std::string, size_t> &textureIndexByName);
    static bool loadCookedHudImage(
        const Engine::AssetFileSystem &assetFileSystem,
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
    // Adds the shared font (SharedFontCache) to fonts: a view of its handles, which the cache owns.
    static bool loadHudFont(
        const Engine::AssetFileSystem *pAssetFileSystem,
        const std::string &fontName,
        std::vector<GameplayHudFontData> &fonts);
    // loadHudFont for several fonts, the missing ones loaded together; false when any failed.
    static bool loadHudFonts(
        const Engine::AssetFileSystem *pAssetFileSystem,
        const std::vector<std::string> &fontNames,
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
    static bgfx::TextureHandle ensureHudTextureColorModulated(
        const GameplayHudTextureData &texture,
        uint32_t colorAbgr,
        std::vector<GameplayHudTextureColorTextureData> &colorTextures);
    // The font's main layer drawn in colorAbgr; white keeps the atlas's own colours.
    static GameplayHudFontLayer hudFontMainLayer(const GameplayHudFontData &font, uint32_t colorAbgr);
    static constexpr size_t TextColorCodeLength = 6;
    // Might and Magic's inline text colour: "\f" and five digits of an R5G6B5 colour; "\f00000" returns to the
    // line's own colour. True when a code starts at `index`; `colorAbgr` is then its colour, or nothing for the line's
    // own.
    static bool readTextColorCode(std::string_view text, size_t index, std::optional<uint32_t> &colorAbgr);
    // Reopens a colour still open at the end of a wrapped line at the start of the next.
    static void carryTextColorsAcrossLines(std::vector<std::string> &lines);
    static float measureHudTextWidth(const GameplayHudFontData &font, const std::string &text);
    static std::string clampHudTextToWidth(const GameplayHudFontData &font, const std::string &text, float maxWidth);
    static std::vector<std::string> wrapHudTextToWidth(
        const GameplayHudFontData &font,
        const std::string &text,
        float maxWidth);
    static void renderHudFontLayer(
        const GameplayHudFontData &font,
        const GameplayHudFontLayer &layer,
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
        const RenderHudFontLayerFn &renderHudFontLayer);
};
} // namespace OpenYAMM::Game
