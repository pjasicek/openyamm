#pragma once

#include "engine/AssetFileSystem.h"
#include "game/IScreen.h"

#include <bgfx/bgfx.h>

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

    void drawTexture(const std::string &textureName, const Rect &rect);
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
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    };

    virtual void drawScreen(float deltaSeconds) = 0;

    void ensureRendererInitialized();
    void destroyRendererResources();
    const TextureHandle *findTexture(const std::string &textureName) const;
    const TextureHandle *ensureTexture(const std::string &textureName);
    std::optional<std::string> resolveTexturePath(const std::string &textureName);

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    int m_frameWidth = 0;
    int m_frameHeight = 0;
    float m_mouseX = 0.0f;
    float m_mouseY = 0.0f;
    float m_mouseWheelDelta = 0.0f;
    bool m_leftMouseDown = false;
    bool m_leftMouseDownPrevious = false;
    bool m_rendererInitialized = false;
    bgfx::ProgramHandle m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureUniformHandle = BGFX_INVALID_HANDLE;
    std::vector<TextureHandle> m_textureHandles;
    std::unordered_map<std::string, size_t> m_textureIndexByName;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> m_directoryEntriesByPath;
    std::unordered_map<std::string, std::optional<std::string>> m_resolvedTexturePaths;
};
}
