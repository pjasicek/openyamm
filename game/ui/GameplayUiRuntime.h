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
#include <optional>
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

struct GameplayHudLoopingAnimationState
{
    bool initialized = false;
    bool advancing = false;
    std::string animationName;
    uint32_t accumulatedSourceTicks = 0;
    uint32_t lastSourceTicks = 0;
};

enum class GameplayUiAssetLoadKind : uint8_t
{
    HudTexture,
    ItemIcon,
    HudFont,
    SolidTexture,
    DynamicTexture,
    HudTextureColor,
    HudTextureColorModulated,
    HudFontColor,
};

struct GameplayUiAssetLoadPerformanceEvent
{
    GameplayUiAssetLoadKind kind = GameplayUiAssetLoadKind::HudTexture;
    std::string name;
    uint64_t loadNanoseconds = 0;
    uint32_t colorAbgr = 0;
    int width = 0;
    int height = 0;
    bool success = false;
    bool hasColor = false;
};

struct GameplayUiOverlayFramePerformanceDiagnostics
{
    bool collected = false;
    uint64_t totalNanoseconds = 0;
    uint64_t beginInspectableFrameNanoseconds = 0;
    uint64_t pendingDialogNanoseconds = 0;
    uint64_t screenFxNanoseconds = 0;
    uint64_t chestBelowNanoseconds = 0;
    uint64_t inventoryBelowNanoseconds = 0;
    uint64_t dialogueBelowNanoseconds = 0;
    uint64_t characterBelowNanoseconds = 0;
    uint64_t hudArtNanoseconds = 0;
    uint64_t hudNanoseconds = 0;
    uint64_t chestAboveNanoseconds = 0;
    uint64_t inventoryAboveNanoseconds = 0;
    uint64_t characterAboveNanoseconds = 0;
    uint64_t dialogueAboveNanoseconds = 0;
    uint64_t restNanoseconds = 0;
    uint64_t menuNanoseconds = 0;
    uint64_t controlsNanoseconds = 0;
    uint64_t keyboardNanoseconds = 0;
    uint64_t videoOptionsNanoseconds = 0;
    uint64_t saveGameNanoseconds = 0;
    uint64_t loadGameNanoseconds = 0;
    uint64_t journalNanoseconds = 0;
    uint64_t quickReferenceNanoseconds = 0;
    uint64_t spellbookNanoseconds = 0;
    uint64_t heldItemNanoseconds = 0;
    uint64_t itemInspectNanoseconds = 0;
    uint64_t mouseLookNanoseconds = 0;
    uint64_t deferredInventoryNanoseconds = 0;
    uint64_t utilitySpellNanoseconds = 0;
    uint64_t characterInspectNanoseconds = 0;
    uint64_t buffInspectNanoseconds = 0;
    uint64_t characterDetailNanoseconds = 0;
    uint64_t actorInspectNanoseconds = 0;
    uint64_t spellInspectNanoseconds = 0;
    uint64_t readableScrollNanoseconds = 0;
};

class GameplayUiRuntime
{
public:
    void beginPerformanceFrame(bool enabled);
    const std::vector<GameplayUiAssetLoadPerformanceEvent> &performanceAssetLoadEvents() const;
    size_t performanceAssetLoadEventOverflowCount() const;
    void setLastOverlayFramePerformanceDiagnostics(
        const GameplayUiOverlayFramePerformanceDiagnostics &diagnostics);
    const GameplayUiOverlayFramePerformanceDiagnostics &lastOverlayFramePerformanceDiagnostics() const;

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
    bool ensureTownPortalDestinationsLoaded(const std::string &currentMapFileName);
    bool ensureDimensionDoorDestinationsLoaded(uint32_t dayIndex, bool crossContinentsUnlocked);
    const std::string &townPortalBackgroundTextureName() const;
    const std::vector<GameplayTownPortalDestination> &townPortalDestinations() const;

    bool loadHudTexture(const std::string &textureName);
    bool loadItemIconTexture(const std::string &textureName);
    bool loadHudFont(const std::string &fontName);
    std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height);
    std::optional<std::vector<uint8_t>> loadItemIconBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height);
    void clearHudLayoutRuntimeHeightOverrides();
    void setHudLayoutRuntimeWidthOverride(const std::string &layoutId, float width);
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height);
    const UiLayoutManager::LayoutElement *findHudLayoutElement(const std::string &layoutId) const;
    int defaultHudLayoutZIndexForScreen(const std::string &screen) const;
    const std::vector<std::string> &sortedHudLayoutIdsForScreen(const std::string &screen) const;
    std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const;
    std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(const std::string &textureName);
    std::optional<GameplayHudTextureHandle> ensureItemIconTextureLoaded(const std::string &textureName);
    std::optional<std::string> iconAnimationFrameTextureName(
        const std::string &animationName,
        uint32_t elapsedTicks) const;
    std::optional<std::string> flyBuffIconAnimationFrameTextureName(bool active, uint32_t tickDivisor);
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
    bool ensureItemIconTextureDimensions(const std::string &textureName, int &width, int &height);
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
    bgfx::TextureHandle ensureHudTextureColorModulated(
        const GameplayHudTextureHandle &texture,
        uint32_t colorAbgr);
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
    void submitHudTexturedQuadRotatedCounterClockwise(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
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
    bool playHouseVideo(const std::string &videoStem, const std::string &videoDirectory);
    void queueBackgroundHouseVideoPreload(const std::string &videoStem);
    void updateHouseVideoBackgroundPreloads();
    void setHouseVideoAudioVolume(float volume);
    void updateHouseVideoPlayback(float deltaSeconds);
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const;
    HouseVideoPlayer::CacheStats houseVideoCacheStats() const;

private:
    void recordPerformanceAssetLoad(
        GameplayUiAssetLoadKind kind,
        const std::string &name,
        uint64_t loadNanoseconds,
        bool success,
        int width,
        int height,
        bool hasColor = false,
        uint32_t colorAbgr = 0);
    void clearHudResources();
    void clearPortraitRuntime();

    struct HudLayoutResolutionCacheKey
    {
        std::string layoutId;
        int screenWidth = 0;
        int screenHeight = 0;
        float fallbackWidth = 0.0f;
        float fallbackHeight = 0.0f;

        bool operator==(const HudLayoutResolutionCacheKey &other) const
        {
            return layoutId == other.layoutId
                && screenWidth == other.screenWidth
                && screenHeight == other.screenHeight
                && fallbackWidth == other.fallbackWidth
                && fallbackHeight == other.fallbackHeight;
        }
    };

    struct HudLayoutResolutionCacheKeyHash
    {
        size_t operator()(const HudLayoutResolutionCacheKey &key) const;
    };

    void clearHudLayoutLookupCaches() const;

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    std::string m_assetWorldId;
    Engine::AssetScaleTier m_uiAssetScaleTier = Engine::AssetScaleTier::X1;
    Engine::AssetScaleTier m_iconAssetScaleTier = Engine::AssetScaleTier::X1;
    Engine::AssetScaleTier m_fontAssetScaleTier = Engine::AssetScaleTier::X1;
    bool m_layoutsLoaded = false;
    bool m_assetsPreloaded = false;
    bool m_portraitRuntimeLoaded = false;
    bool m_houseVideoPlayerInitialized = false;
    bool m_performanceFrameEnabled = false;
    size_t m_performanceAssetLoadEventOverflowCount = 0;
    std::vector<GameplayUiAssetLoadPerformanceEvent> m_performanceAssetLoadEvents;
    GameplayUiOverlayFramePerformanceDiagnostics m_lastOverlayFramePerformanceDiagnostics = {};
    const GameDataRepository *m_pDataRepository = nullptr;
    GameplayAssetLoadCache m_assetLoadCache;
    UiLayoutManager m_layoutManager;
    mutable std::unordered_map<std::string, const UiLayoutManager::LayoutElement *> m_hudLayoutElementLookupCache;
    mutable std::unordered_map<
        HudLayoutResolutionCacheKey,
        std::optional<GameplayResolvedHudLayoutElement>,
        HudLayoutResolutionCacheKeyHash> m_hudLayoutResolutionCache;
    std::vector<GameplayHudTextureData> m_hudTextureHandles;
    std::unordered_map<std::string, size_t> m_hudTextureIndexByName;
    std::vector<GameplayHudFontData> m_hudFontHandles;
    std::vector<GameplayHudFontColorTextureData> m_hudFontColorTextureHandles;
    std::vector<GameplayHudTextureColorTextureData> m_hudTextureColorTextureHandles;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeWidthOverrides;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
    GameplayHudScreenState m_renderedInspectableHudScreenState = GameplayHudScreenState::Gameplay;
    std::string m_townPortalDestinationsMapFileName;
    std::string m_townPortalBackgroundTextureName;
    std::vector<GameplayTownPortalDestination> m_townPortalDestinations;
    bool m_townPortalDestinationsLoaded = false;
    GameplayHudRenderBackend m_hudRenderBackend;
    std::vector<GameplayPortraitFxState> m_portraitFxStates;
    GameplayPortraitPresentationState m_portraitPresentationState;
    GameplayHudLoopingAnimationState m_flyBuffIconAnimationState;
    HouseVideoPlayer m_houseVideoPlayer;
};
}
