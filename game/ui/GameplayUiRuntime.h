#pragma once

#include "engine/AssetFileSystem.h"
#include "game/audio/HouseVideoPlayer.h"
#include "game/data/GameDataRepository.h"
#include "game/events/EventRuntime.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpeechIds.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/ui/GameplayHudArcMesh.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayHudLayoutCache.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ActorModelPreview;
class IGameplayWorldRuntime;
class SpriteAtlasCache;

struct GameplayHudRenderBackend
{
    bgfx::ProgramHandle texturedProgramHandle = BGFX_INVALID_HANDLE;
    // Draws quads multiplied by tintUniformHandle, such as coloured text.
    bgfx::ProgramHandle tintedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle tintUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle textureSamplerHandle = BGFX_INVALID_HANDLE;
    uint16_t viewId = 2;
};

// A solid colour's texel in the shared HUD palette texture.
struct GameplayHudPaletteColor
{
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    float u = 0.0f;
    float v = 0.0f;
};

// A batch quad drawn in a palette colour.
GameplayHudBatchQuad gameplayHudPaletteQuad(
    const GameplayHudPaletteColor &color, float x, float y, float width, float height);

struct GameplayPortraitFxState
{
    bool active = false;
    size_t animationId = 0;
    uint32_t startedTicks = 0;
};

struct GameplayPortraitMeterState
{
    float health = -1.0f;
    float damageFrom = 0.0f;
    float recoveryMaximum = 0.0f;
    uint32_t damagedTicks = 0;
};

struct GameplayPortraitPresentationState
{
    std::array<GameplayPortraitMeterState, 5> meters;
    uint32_t lastAnimationUpdateTicks = 0;
    std::vector<uint32_t> memberSpeechCooldownUntilTicks;
    std::vector<uint32_t> memberCombatSpeechCooldownUntilTicks;
    // When each member last said each line, for the "Repeated voice lines" setting.
    std::vector<std::unordered_map<SpeechId, uint32_t>> memberSpeechLastPlayedTicks;
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
    void bindSpriteAtlasCache(SpriteAtlasCache &cache);
    void bindActorModelPreview(ActorModelPreview &preview);
    const Engine::AssetFileSystem *assetFileSystem() const;

    bool ensureGameplayLayoutsLoaded(const GameplayUiController &uiController);
    void preloadReferencedAssets();

    GameplayAssetLoadCache &assetLoadCache();
    const GameplayAssetLoadCache &assetLoadCache() const;

    const std::vector<GameplayHudLayoutEntry> &gameplayHudLayoutEntries();
    UiLayoutManager &layoutManager();
    const UiLayoutManager &layoutManager() const;

    std::vector<GameplayHudTextureData> &hudTextureHandles();
    const std::vector<GameplayHudTextureData> &hudTextureHandles() const;

    std::unordered_map<std::string, size_t> &hudTextureIndexByName();
    const std::unordered_map<std::string, size_t> &hudTextureIndexByName() const;

    std::vector<GameplayHudFontData> &hudFontHandles();
    const std::vector<GameplayHudFontData> &hudFontHandles() const;

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
        int &height,
        Engine::AssetScaleTier *pLoadedTier = nullptr);
    std::optional<std::vector<uint8_t>> loadItemIconBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height,
        Engine::AssetScaleTier *pLoadedTier = nullptr);
    std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgraCached(
        const std::string &textureName,
        int16_t paletteId,
        int &width,
        int &height,
        Engine::AssetScaleTier *pLoadedTier = nullptr);
    void clearHudLayoutRuntimeHeightOverrides();
    void setHudLayoutRuntimeWidthOverride(const std::string &layoutId, float width);
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height);
    const UiLayoutManager::LayoutElement *findHudLayoutElement(const std::string &layoutId) const;

    template <size_t Size>
    const UiLayoutManager::LayoutElement *findHudLayoutElement(const char (&layoutId)[Size]) const
    {
        return findStaticHudLayoutElement(layoutId);
    }

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
        std::optional<uint32_t> elapsedTicks = std::nullopt) const;
    std::optional<std::string> flyBuffIconAnimationFrameTextureName(bool active, uint32_t tickDivisor);
    std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        const std::string &textureName,
        uint32_t abgrColor);
    // Solid colours (minimap lines and markers) share one palette texture: a quad whose UVs all lie on a colour's
    // texel draws in that colour, so quads of different colours batch into one draw.
    std::optional<GameplayHudPaletteColor> ensureHudPaletteColor(uint32_t abgrColor);
    std::optional<GameplayHudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels);
    std::optional<GameplayHudTextureHandle> findCachedDynamicHudTexture(
        const std::string &textureName,
        const std::string &contentSignature) const;
    void setDynamicHudTextureContentSignature(
        const std::string &textureName,
        const std::string &contentSignature);
    // Returns physical pixel dimensions matching the BGRA buffer, independent of the logical HUD size.
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
    GameplayHudFontLayer hudFontMainLayer(const GameplayHudFontHandle &font, uint32_t colorAbgr) const;
    void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item);
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y);
    void releaseHudGpuResources(bool destroyBgfxResources);
    void bindHudRenderBackend(const GameplayHudRenderBackend &backend);
    void clearHudRenderBackend();
    bool hasHudRenderResources() const;
    void prepareHudView(int width, int height) const;
    std::array<float, 2> hudTextureUvScale(bgfx::TextureHandle textureHandle) const;
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
        TextureFilterProfile filterProfile = TextureFilterProfile::Ui,
        float rotationRadians = 0.0f) const;
    void submitHudTexturedEllipse(
        bgfx::TextureHandle textureHandle, float x, float y, float width, float height,
        float u0 = 0.0f, float v0 = 0.0f, float u1 = 1.0f, float v1 = 1.0f) const;
    // `uRepeat` tiles the texture that many times along the drawn range (a wrapping pattern such as hatching).
    void submitHudTexturedArc(bgfx::TextureHandle textureHandle,
        const GameplayResolvedHudLayoutElement &rect, float strokeWidth, float startDegrees, float sweepDegrees,
        float begin = 0, float end = 1, float uRepeat = 1) const;
    uint32_t actorInspectAnimationTicks(bool visible, uint32_t nowTicks);
    // The inspected actor's 3D portrait when it has a model, otherwise its sprite (name, palette).
    void renderActorInspectPreview(const IGameplayWorldRuntime &world, size_t actorIndex, uint32_t animationTicks,
        const std::string &name, int16_t paletteId, const GameplayResolvedHudLayoutElement &rect, float scale,
        int yOffset);
    void submitHudTexturedQuadRotatedCounterClockwise(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        TextureFilterProfile filterProfile = TextureFilterProfile::Ui) const;
    void submitHudQuadBatch(
        std::span<const GameplayHudBatchQuad> quads,
        TextureFilterProfile filterProfile = TextureFilterProfile::Ui) const;
    void submitWorldHudQuadBatch(std::span<const GameplayHudBatchQuad> quads,
        uint16_t viewId, const bx::Vec3 &origin, const bx::Vec3 &right, const bx::Vec3 &up,
        TextureFilterProfile filterProfile = TextureFilterProfile::UiIllustration) const;
    // The textured program, or the tinted one with its colour set for the next submit.
    bgfx::ProgramHandle hudProgramForTint(uint32_t tintAbgr) const;
    void renderHudFontLayer(
        const GameplayHudFontHandle &font,
        const GameplayHudFontLayer &layer,
        const std::string &text,
        float textX,
        float textY,
        float fontScale,
        const GameplayResolvedHudLayoutElement *pClip = nullptr) const;
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
    void setHouseVideoAudioVolume(float volume);
    void updateHouseVideoPlayback(float deltaSeconds);
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const;

private:
    void registerHudTextureUvScales(size_t firstTexture);
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
    };

    // Looks the cache up without copying the layout id (the HUD resolves many elements every frame).
    struct HudLayoutResolutionCacheView
    {
        std::string_view layoutId;
        int screenWidth = 0;
        int screenHeight = 0;
        float fallbackWidth = 0.0f;
        float fallbackHeight = 0.0f;
    };

    struct HudLayoutResolutionCacheKeyHash
    {
        using is_transparent = void;
        size_t operator()(const HudLayoutResolutionCacheKey &key) const;
        size_t operator()(const HudLayoutResolutionCacheView &key) const;
    };

    struct HudLayoutResolutionCacheKeyEqual
    {
        using is_transparent = void;
        template <typename First, typename Second>
        bool operator()(const First &first, const Second &second) const
        {
            return first.layoutId == second.layoutId
                && first.screenWidth == second.screenWidth
                && first.screenHeight == second.screenHeight
                && first.fallbackWidth == second.fallbackWidth
                && first.fallbackHeight == second.fallbackHeight;
        }
    };

    const UiLayoutManager::LayoutElement *findStaticHudLayoutElement(const char *pLayoutId) const;
    void clearHudLayoutLookupCaches() const;

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    std::string m_assetWorldId;
    Engine::AssetScaleTier m_iconAssetScaleTier = Engine::AssetScaleTier::X1;
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
    GameplayHudLayoutCache m_gameplayHudLayoutCache;
    mutable std::unordered_map<std::string, const UiLayoutManager::LayoutElement *> m_hudLayoutElementLookupCache;
    mutable std::unordered_map<const char *, const UiLayoutManager::LayoutElement *>
        m_staticHudLayoutElementLookupCache;
    mutable std::unordered_map<
        HudLayoutResolutionCacheKey,
        std::optional<GameplayResolvedHudLayoutElement>,
        HudLayoutResolutionCacheKeyHash,
        HudLayoutResolutionCacheKeyEqual> m_hudLayoutResolutionCache;
    std::vector<GameplayHudTextureData> m_hudTextureHandles;
    // UV scales of cooked HUD art padded to whole 4x4 blocks, by texture handle (see GameplayHudTextureData::uScale).
    std::unordered_map<uint16_t, std::array<float, 2>> m_hudTextureUvScales;
    std::unordered_map<std::string, size_t> m_hudTextureIndexByName;
    std::unordered_map<std::string, std::string> m_dynamicHudTextureContentSignatures;
    std::vector<GameplayHudFontData> m_hudFontHandles;
    std::vector<GameplayHudTextureColorTextureData> m_hudTextureColorTextureHandles;
    bgfx::TextureHandle m_hudPaletteTextureHandle = BGFX_INVALID_HANDLE;
    std::unordered_map<uint32_t, uint16_t> m_hudPaletteSlotByColor;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeWidthOverrides;
    std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
    GameplayHudScreenState m_renderedInspectableHudScreenState = GameplayHudScreenState::Gameplay;
    std::string m_townPortalDestinationsMapFileName;
    std::string m_townPortalBackgroundTextureName;
    std::vector<GameplayTownPortalDestination> m_townPortalDestinations;
    bool m_townPortalDestinationsLoaded = false;
    GameplayHudRenderBackend m_hudRenderBackend;
    mutable HudArcMeshCache m_hudArcMeshCache;
    SpriteAtlasCache *m_pSpriteAtlasCache = nullptr;
    ActorModelPreview *m_pActorModelPreview = nullptr;
    GameplayActorInspectClock m_actorInspectClock;
    std::array<bgfx::UniformHandle, 6> m_previewUniforms = {{
        BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE,
        BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    std::vector<GameplayPortraitFxState> m_portraitFxStates;
    GameplayPortraitPresentationState m_portraitPresentationState;
    GameplayHudLoopingAnimationState m_flyBuffIconAnimationState;
    HouseVideoPlayer m_houseVideoPlayer;
};
}
