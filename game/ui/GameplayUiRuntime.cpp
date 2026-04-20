#include "game/ui/GameplayUiRuntime.h"

#include <bgfx/bgfx.h>

namespace OpenYAMM::Game
{
void GameplayUiRuntime::clear()
{
    clearHudResources();
    m_layoutManager.clear();
    m_hudLayoutRuntimeHeightOverrides.clear();
    m_renderedInspectableHudItems.clear();
    m_assetLoadCache = {};
    m_pAssetFileSystem = nullptr;
    m_layoutsLoaded = false;
    m_assetsPreloaded = false;
}

void GameplayUiRuntime::bindAssetFileSystem(const Engine::AssetFileSystem *pAssetFileSystem)
{
    if (m_pAssetFileSystem == pAssetFileSystem)
    {
        return;
    }

    clear();
    m_pAssetFileSystem = pAssetFileSystem;
}

const Engine::AssetFileSystem *GameplayUiRuntime::assetFileSystem() const
{
    return m_pAssetFileSystem;
}

bool GameplayUiRuntime::ensureGameplayLayoutsLoaded(const GameplayUiController &uiController)
{
    if (m_layoutsLoaded)
    {
        return true;
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    m_layoutManager.clear();

    const bool loaded = uiController.loadGameplayLayouts(
        *m_pAssetFileSystem,
        [this](const std::string &path) -> bool
        {
            return m_layoutManager.loadLayoutFile(*m_pAssetFileSystem, path);
        });

    if (!loaded)
    {
        return false;
    }

    m_layoutsLoaded = true;
    return true;
}

void GameplayUiRuntime::preloadReferencedAssets()
{
    if (m_assetsPreloaded)
    {
        return;
    }

    for (const auto &[id, element] : m_layoutManager.elements())
    {
        (void)id;

        for (const std::string *pAssetName : {
                 &element.primaryAsset,
                 &element.hoverAsset,
                 &element.pressedAsset,
                 &element.secondaryAsset,
                 &element.tertiaryAsset,
                 &element.quaternaryAsset,
                 &element.quinaryAsset})
        {
            if (!pAssetName->empty())
            {
                loadHudTexture(*pAssetName);
            }
        }

        if (!element.fontName.empty())
        {
            loadHudFont(element.fontName);
        }
    }

    m_assetsPreloaded = true;
}

GameplayAssetLoadCache &GameplayUiRuntime::assetLoadCache()
{
    return m_assetLoadCache;
}

const GameplayAssetLoadCache &GameplayUiRuntime::assetLoadCache() const
{
    return m_assetLoadCache;
}

UiLayoutManager &GameplayUiRuntime::layoutManager()
{
    return m_layoutManager;
}

const UiLayoutManager &GameplayUiRuntime::layoutManager() const
{
    return m_layoutManager;
}

std::vector<GameplayHudTextureData> &GameplayUiRuntime::hudTextureHandles()
{
    return m_hudTextureHandles;
}

const std::vector<GameplayHudTextureData> &GameplayUiRuntime::hudTextureHandles() const
{
    return m_hudTextureHandles;
}

std::unordered_map<std::string, size_t> &GameplayUiRuntime::hudTextureIndexByName()
{
    return m_hudTextureIndexByName;
}

const std::unordered_map<std::string, size_t> &GameplayUiRuntime::hudTextureIndexByName() const
{
    return m_hudTextureIndexByName;
}

std::vector<GameplayHudFontData> &GameplayUiRuntime::hudFontHandles()
{
    return m_hudFontHandles;
}

const std::vector<GameplayHudFontData> &GameplayUiRuntime::hudFontHandles() const
{
    return m_hudFontHandles;
}

std::vector<GameplayHudFontColorTextureData> &GameplayUiRuntime::hudFontColorTextureHandles()
{
    return m_hudFontColorTextureHandles;
}

const std::vector<GameplayHudFontColorTextureData> &GameplayUiRuntime::hudFontColorTextureHandles() const
{
    return m_hudFontColorTextureHandles;
}

std::vector<GameplayHudTextureColorTextureData> &GameplayUiRuntime::hudTextureColorTextureHandles()
{
    return m_hudTextureColorTextureHandles;
}

const std::vector<GameplayHudTextureColorTextureData> &GameplayUiRuntime::hudTextureColorTextureHandles() const
{
    return m_hudTextureColorTextureHandles;
}

std::unordered_map<std::string, float> &GameplayUiRuntime::hudLayoutRuntimeHeightOverrides()
{
    return m_hudLayoutRuntimeHeightOverrides;
}

const std::unordered_map<std::string, float> &GameplayUiRuntime::hudLayoutRuntimeHeightOverrides() const
{
    return m_hudLayoutRuntimeHeightOverrides;
}

std::vector<GameplayRenderedInspectableHudItem> &GameplayUiRuntime::renderedInspectableHudItems()
{
    return m_renderedInspectableHudItems;
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayUiRuntime::renderedInspectableHudItems() const
{
    return m_renderedInspectableHudItems;
}

void GameplayUiRuntime::clearRenderedInspectableHudItems()
{
    m_renderedInspectableHudItems.clear();
}

bool GameplayUiRuntime::loadHudTexture(const std::string &textureName)
{
    return GameplayHudCommon::loadHudTexture(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        m_hudTextureHandles,
        m_hudTextureIndexByName);
}

bool GameplayUiRuntime::loadHudFont(const std::string &fontName)
{
    return GameplayHudCommon::loadHudFont(
        m_pAssetFileSystem,
        m_assetLoadCache,
        fontName,
        m_hudFontHandles);
}

std::optional<std::vector<uint8_t>> GameplayUiRuntime::loadHudBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height)
{
    return GameplayHudCommon::loadHudBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_assetLoadCache,
        textureName,
        width,
        height);
}

void GameplayUiRuntime::clearHudResources()
{
    for (GameplayHudTextureData &textureHandle : m_hudTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (GameplayHudFontData &fontHandle : m_hudFontHandles)
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (GameplayHudFontColorTextureData &textureHandle : m_hudFontColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (GameplayHudTextureColorTextureData &textureHandle : m_hudTextureColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudTextureHandles.clear();
    m_hudTextureIndexByName.clear();
    m_hudFontHandles.clear();
    m_hudFontColorTextureHandles.clear();
    m_hudTextureColorTextureHandles.clear();
}
}
