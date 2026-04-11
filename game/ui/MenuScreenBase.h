#pragma once

#include "engine/AssetFileSystem.h"
#include "game/ui/IScreen.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MenuScreenBase : public IScreen
{
public:
    struct Rect
    {
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
    };

    struct SourceRect
    {
        float x = 0.0f;
        float y = 0.0f;
        float width = 0.0f;
        float height = 0.0f;
    };

    struct TextureSize
    {
        float width = 0.0f;
        float height = 0.0f;
    };

    struct ButtonVisualSet
    {
        std::string defaultTextureName;
        std::string highlightedTextureName;
        std::string pressedTextureName;
    };

    struct ButtonState
    {
        bool hovered = false;
        bool pressed = false;
        bool clicked = false;
    };

    explicit MenuScreenBase(const Engine::AssetFileSystem &assetFileSystem);
    ~MenuScreenBase() override;

    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds) override;

protected:
    const Engine::AssetFileSystem &assetFileSystem() const;
    int frameWidth() const;
    int frameHeight() const;
    float mouseX() const;
    float mouseY() const;
    float mouseWheelDelta() const;
    bool leftMouseDown() const;
    bool leftMouseJustPressed() const;
    bool leftMouseJustReleased() const;
    bool rightMouseDown() const;
    bool rightMouseJustPressed() const;
    bool rightMouseJustReleased() const;

    void drawTexture(const std::string &textureName, const Rect &rect);
    void drawTextureRegion(const std::string &textureName, const SourceRect &sourceRect, const Rect &rect);
    void drawTextureColor(const std::string &textureName, const Rect &rect, uint32_t colorAbgr);
    void drawPixelsBgra(
        const std::string &cacheKey,
        int width,
        int height,
        const std::vector<uint8_t> &pixelsBgra,
        const Rect &rect);
    void drawTextureHandle(bgfx::TextureHandle textureHandle, const Rect &rect);
    void drawTextureRegionColor(
        const std::string &textureName,
        const SourceRect &sourceRect,
        const Rect &rect,
        uint32_t colorAbgr);
    std::optional<TextureSize> textureSize(const std::string &textureName);
    bool drawText(
        const std::string &fontName,
        const std::string &text,
        float pixelX,
        float pixelY,
        uint32_t colorAbgr = 0xffffffffu,
        float scale = 1.0f,
        bool drawShadow = true);
    float measureTextWidth(const std::string &fontName, const std::string &text, float scale = 1.0f);
    int fontHeight(const std::string &fontName);
    ButtonState drawButton(const ButtonVisualSet &visuals, const Rect &rect);
    void drawDebugText(int pixelX, int pixelY, uint8_t color, const std::string &text) const;
    bool hitTest(const Rect &rect) const;

private:
    struct MenuVertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;

        static void init();

        static bgfx::VertexLayout ms_layout;
    };

    struct TextureHandle
    {
        std::string normalizedTextureName;
        int width = 0;
        int height = 0;
        int physicalWidth = 0;
        int physicalHeight = 0;
        std::vector<uint8_t> bgraPixels;
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    };

    struct TextureColorHandle
    {
        std::string normalizedTextureName;
        uint32_t colorAbgr = 0xffffffffu;
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    };

    struct DynamicTextureHandle
    {
        std::string cacheKey;
        int width = 0;
        int height = 0;
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    };

    struct FontGlyphMetrics
    {
        int leftSpacing = 0;
        int width = 0;
        int rightSpacing = 0;
    };

    struct FontHandle
    {
        std::string normalizedFontName;
        int firstChar = 0;
        int lastChar = 0;
        int fontHeight = 0;
        int atlasCellWidth = 0;
        int atlasWidth = 0;
        int atlasHeight = 0;
        std::array<FontGlyphMetrics, 256> glyphMetrics = {{}};
        std::vector<uint8_t> mainAtlasPixels;
        bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
    };

    struct FontColorHandle
    {
        std::string normalizedFontName;
        uint32_t colorAbgr = 0xffffffffu;
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    };

    virtual void drawScreen(float deltaSeconds) = 0;

    void ensureRendererInitialized();
    void destroyRendererResources();
    const TextureHandle *findTexture(const std::string &textureName) const;
    const TextureHandle *ensureTexture(const std::string &textureName);
    const FontHandle *findFont(const std::string &fontName) const;
    const FontHandle *ensureFont(const std::string &fontName);
    bgfx::TextureHandle ensureDynamicTexture(
        const std::string &cacheKey,
        int width,
        int height,
        const std::vector<uint8_t> &pixelsBgra);
    bgfx::TextureHandle ensureTextureColor(const TextureHandle &texture, uint32_t colorAbgr);
    bgfx::TextureHandle ensureFontColor(const FontHandle &font, uint32_t colorAbgr);
    std::optional<std::string> resolveTexturePath(const std::string &textureName);
    std::optional<std::string> resolveFontPath(const std::string &fontName);

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    int m_frameWidth = 0;
    int m_frameHeight = 0;
    float m_mouseX = 0.0f;
    float m_mouseY = 0.0f;
    float m_mouseWheelDelta = 0.0f;
    bool m_leftMouseDown = false;
    bool m_leftMouseDownPrevious = false;
    bool m_rightMouseDown = false;
    bool m_rightMouseDownPrevious = false;
    bool m_rendererInitialized = false;
    bgfx::ProgramHandle m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureUniformHandle = BGFX_INVALID_HANDLE;
    std::vector<TextureHandle> m_textureHandles;
    std::vector<TextureColorHandle> m_textureColorHandles;
    std::vector<DynamicTextureHandle> m_dynamicTextureHandles;
    std::vector<FontHandle> m_fontHandles;
    std::vector<FontColorHandle> m_fontColorHandles;
    std::unordered_map<std::string, size_t> m_textureIndexByName;
    std::unordered_map<std::string, size_t> m_fontIndexByName;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> m_directoryEntriesByPath;
    std::unordered_map<std::string, std::optional<std::string>> m_resolvedTexturePaths;
    std::unordered_map<std::string, std::optional<std::string>> m_resolvedFontPaths;
};
}
