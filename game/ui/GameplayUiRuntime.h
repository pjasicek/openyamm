#pragma once

#include "engine/AssetFileSystem.h"
#include "game/audio/HouseVideoPlayer.h"
#include "game/data/GameDataRepository.h"
#include "game/events/EventRuntime.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct GameplayHudRenderBackend
{
    bgfx::ProgramHandle texturedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle textureSamplerHandle = BGFX_INVALID_HANDLE;
    uint16_t viewId = 2;
};

struct GameplayPortraitFxState
{
    bool active = false;
    size_t animationId = 0;
    uint32_t startedTicks = 0;
};

struct GameplayPortraitPresentationState
{
    uint32_t lastAnimationUpdateTicks = 0;
    std::vector<uint32_t> memberSpeechCooldownUntilTicks;
    std::vector<uint32_t> memberCombatSpeechCooldownUntilTicks;
};

class GameplayUiRuntime
{
public:
    void clear();
    void bindDataRepository(const GameDataRepository *pDataRepository);
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
    GameplayHudScreenState renderedInspectableHudScreenState() const;
    void setRenderedInspectableHudScreenState(GameplayHudScreenState state);
    bool ensureTownPortalDestinationsLoaded();
    const std::vector<GameplayTownPortalDestination> &townPortalDestinations() const;

    bool loadHudTexture(const std::string &textureName);
    bool loadHudFont(const std::string &fontName);
    std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height);
    void clearHudLayoutRuntimeHeightOverrides();
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height);
    const UiLayoutManager::LayoutElement *findHudLayoutElement(const std::string &layoutId) const;
    int defaultHudLayoutZIndexForScreen(const std::string &screen) const;
    std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const;
    std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const;
    std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(const std::string &textureName);
    std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        const std::string &textureName,
        uint32_t abgrColor);
    std::optional<GameplayHudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels);
    const std::vector<uint8_t> *hudTexturePixels(const std::string &textureName, int &width, int &height);
    bool ensureHudTextureDimensions(const std::string &textureName, int &width, int &height);
    bool tryGetOpaqueHudTextureBounds(
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY);
    std::optional<GameplayHudFontHandle> findHudFont(const std::string &fontName);
    float measureHudTextWidth(const GameplayHudFontHandle &font, const std::string &text) const;
    std::vector<std::string> wrapHudTextToWidth(
        const GameplayHudFontHandle &font,
        const std::string &text,
        float maxWidth) const;
    bgfx::TextureHandle ensureHudTextureColor(const GameplayHudTextureHandle &texture, uint32_t colorAbgr);
    bgfx::TextureHandle ensureHudFontMainTextureColor(const GameplayHudFontHandle &font, uint32_t colorAbgr);
    void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item);
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y);
    void releaseHudGpuResources(bool destroyBgfxResources);
    void bindHudRenderBackend(const GameplayHudRenderBackend &backend);
    void clearHudRenderBackend();
    bool hasHudRenderResources() const;
    void prepareHudView(int width, int height) const;
    void submitHudTexturedQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0 = 0.0f,
        float v0 = 0.0f,
        float u1 = 1.0f,
        float v1 = 1.0f,
        TextureFilterProfile filterProfile = TextureFilterProfile::Ui) const;
    void submitHudQuadBatch(
        const std::vector<GameplayHudBatchQuad> &quads,
        int screenWidth,
        int screenHeight) const;
    void renderHudFontLayer(
        const GameplayHudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;
    bool ensurePortraitRuntimeLoaded();
    void resetPortraitFxStates(size_t memberCount);
    void resetPortraitPresentationState(size_t memberCount);
    GameplayPortraitPresentationState &portraitPresentationState();
    const GameplayPortraitPresentationState &portraitPresentationState() const;
    std::string resolvePortraitTextureName(const Character &character) const;
    bool triggerPortraitFxAnimation(const std::string &animationName, const std::vector<size_t> &memberIndices);
    void triggerPortraitSpellFx(const PartySpellCastResult &result);
    const PortraitFxEventEntry *findPortraitFxEvent(PortraitFxEventKind kind) const;
    const FaceAnimationEntry *findFaceAnimation(FaceAnimationId animationId) const;
    uint32_t defaultPortraitAnimationLengthTicks(PortraitId portraitId) const;
    void renderPortraitFx(
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight) const;
    bool initializeHouseVideoPlayer();
    void shutdownHouseVideoPlayer();
    void stopHouseVideoPlayback();
    bool playHouseVideo(const std::string &videoStem);
    void queueBackgroundHouseVideoPreload(const std::string &videoStem);
    void updateHouseVideoBackgroundPreloads();
    void updateHouseVideoPlayback(float deltaSeconds);
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const;

private:
    void clearHudResources();
    void clearPortraitRuntime();

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    bool m_layoutsLoaded = false;
    bool m_assetsPreloaded = false;
    bool m_portraitRuntimeLoaded = false;
    bool m_houseVideoPlayerInitialized = false;
    const GameDataRepository *m_pDataRepository = nullptr;
    GameplayAssetLoadCache m_assetLoadCache;
    UiLayoutManager m_layoutManager;
    std::vector<GameplayHudTextureData> m_hudTextureHandles;
    std::unordered_map<std::string, size_t> m_hudTextureIndexByName;
    std::vector<GameplayHudFontData> m_hudFontHandles;
    std::vector<GameplayHudFontColorTextureData> m_hudFontColorTextureHandles;
    std::vector<GameplayHudTextureColorTextureData> m_hudTextureColorTextureHandles;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
    GameplayHudScreenState m_renderedInspectableHudScreenState = GameplayHudScreenState::Gameplay;
    std::vector<GameplayTownPortalDestination> m_townPortalDestinations;
    bool m_townPortalDestinationsLoaded = false;
    GameplayHudRenderBackend m_hudRenderBackend;
    std::vector<GameplayPortraitFxState> m_portraitFxStates;
    GameplayPortraitPresentationState m_portraitPresentationState;
    HouseVideoPlayer m_houseVideoPlayer;
};
}
