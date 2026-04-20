#pragma once

#include "engine/AssetFileSystem.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayUiRuntime
{
public:
    void clear();
    void bindAssetFileSystem(const Engine::AssetFileSystem *pAssetFileSystem);
    const Engine::AssetFileSystem *assetFileSystem() const;

    bool ensureGameplayLayoutsLoaded(const GameplayUiController &uiController);
    void preloadReferencedAssets();

    GameplayAssetLoadCache &assetLoadCache();
    const GameplayAssetLoadCache &assetLoadCache() const;

    UiLayoutManager &layoutManager();
    const UiLayoutManager &layoutManager() const;

    std::vector<GameplayHudTextureData> &hudTextureHandles();
    const std::vector<GameplayHudTextureData> &hudTextureHandles() const;

    std::unordered_map<std::string, size_t> &hudTextureIndexByName();
    const std::unordered_map<std::string, size_t> &hudTextureIndexByName() const;

    std::vector<GameplayHudFontData> &hudFontHandles();
    const std::vector<GameplayHudFontData> &hudFontHandles() const;

    std::vector<GameplayHudFontColorTextureData> &hudFontColorTextureHandles();
    const std::vector<GameplayHudFontColorTextureData> &hudFontColorTextureHandles() const;

    std::vector<GameplayHudTextureColorTextureData> &hudTextureColorTextureHandles();
    const std::vector<GameplayHudTextureColorTextureData> &hudTextureColorTextureHandles() const;

    std::unordered_map<std::string, float> &hudLayoutRuntimeHeightOverrides();
    const std::unordered_map<std::string, float> &hudLayoutRuntimeHeightOverrides() const;

    std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems();
    const std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems() const;
    void clearRenderedInspectableHudItems();

    bool loadHudTexture(const std::string &textureName);
    bool loadHudFont(const std::string &fontName);
    std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height);

private:
    void clearHudResources();

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    bool m_layoutsLoaded = false;
    bool m_assetsPreloaded = false;
    GameplayAssetLoadCache m_assetLoadCache;
    UiLayoutManager m_layoutManager;
    std::vector<GameplayHudTextureData> m_hudTextureHandles;
    std::unordered_map<std::string, size_t> m_hudTextureIndexByName;
    std::vector<GameplayHudFontData> m_hudFontHandles;
    std::vector<GameplayHudFontColorTextureData> m_hudFontColorTextureHandles;
    std::vector<GameplayHudTextureColorTextureData> m_hudTextureColorTextureHandles;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
};
}
