#pragma once

#include "engine/AssetFileSystem.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayOverlayAdapters.h"
#include "game/ui/UiLayoutManager.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class GameSession;
struct ArcomageLibrary;
class IndoorDebugRenderer;
class IndoorPartyRuntime;
class IndoorSceneRuntime;
class GameplayOverlayContext;

using IndoorSpellbookPointerTargetType = GameplaySpellbookPointerTargetType;
using IndoorSpellbookPointerTarget = GameplaySpellbookPointerTarget;
using IndoorCharacterPointerTargetType = GameplayCharacterPointerTargetType;
using IndoorCharacterPointerTarget = GameplayCharacterPointerTarget;

class IndoorGameView
    : public IGameplayOverlaySceneAdapter
    , public IGameplayOverlayHudAdapter
{
public:
    explicit IndoorGameView(GameSession &gameSession);

    bool initialize(
        const Engine::AssetFileSystem &assetFileSystem,
        const MapStatsEntry &map,
        IndoorDebugRenderer &indoorRenderer,
        IndoorSceneRuntime &sceneRuntime,
        GameAudioSystem *pGameAudioSystem);
    void setSettingsSnapshot(const GameSettings &settings);
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    void reopenMenuScreen();

    IndoorPartyRuntime *partyRuntime() const;
    IGameplayWorldRuntime *worldRuntime() const;
    GameAudioSystem *audioSystem() const;
    const ItemTable *itemTable() const;
    const StandardItemEnchantTable *standardItemEnchantTable() const;
    const SpecialItemEnchantTable *specialItemEnchantTable() const;
    const ClassSkillTable *classSkillTable() const;
    const CharacterDollTable *characterDollTable() const;
    const CharacterInspectTable *characterInspectTable() const;
    const RosterTable *rosterTable() const;
    const ReadableScrollTable *readableScrollTable() const;
    const ItemEquipPosTable *itemEquipPosTable() const;
    const SpellTable *spellTable() const;
    const HouseTable *houseTable() const;
    const ChestTable *chestTable() const;
    const NpcDialogTable *npcDialogTable() const;
    const JournalQuestTable *journalQuestTable() const;
    const JournalHistoryTable *journalHistoryTable() const;
    const JournalAutonoteTable *journalAutonoteTable() const;
    const std::string &currentMapFileName() const override;
    float gameplayCameraYawRadians() const override;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override;
    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady) override;
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void executeActiveDialogAction() override;
    bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) override;
    void updateReadableScrollOverlayForHeldItem(
        size_t memberIndex,
        const GameplayCharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed);
    void closeReadableScrollOverlay();
    void closeInventoryNestedOverlay();
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation) override;
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) override;
    bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) override;
    GameSettings &mutableSettings();
    std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState();
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;
    bool trySaveToSelectedGameSlot() override;
    int restFoodRequired() const override;
    const GameSettings &settingsSnapshot() const;
    bool isControlsRenderButtonPressed(GameplayControlsRenderButton button) const;
    bool isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const;
    void clearHudLayoutRuntimeHeightOverrides() override;
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height) override;
    const HouseEntry *findHouseEntry(uint32_t houseId) const;
    const UiLayoutManager::LayoutElement *findHudLayoutElement(const std::string &layoutId) const override;
    int defaultHudLayoutZIndexForScreen(const std::string &screen) const override;
    GameplayHudScreenState currentGameplayHudScreenState() const override;
    std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const override;
    std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const override;
    std::optional<GameplayResolvedHudLayoutElement> resolveGameplayChestGridArea(int width, int height) const override;
    std::optional<GameplayResolvedHudLayoutElement> resolveGameplayInventoryNestedOverlayGridArea(
        int width,
        int height) const override;
    std::optional<GameplayResolvedHudLayoutElement> resolveGameplayHouseShopOverlayFrame(
        int width,
        int height) const override;
    bool isPointerInsideResolvedElement(
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY) const override;
    std::optional<std::string> resolveInteractiveAssetName(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed) const override;
    std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(const std::string &textureName) override;
    std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        const std::string &textureName,
        uint32_t abgrColor) override;
    std::optional<GameplayHudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels) override;
    const std::vector<uint8_t> *hudTexturePixels(
        const std::string &textureName,
        int &width,
        int &height) override;
    bool ensureHudTextureDimensions(const std::string &textureName, int &width, int &height) override;
    bool tryGetOpaqueHudTextureBounds(
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY) override;
    void submitHudTexturedQuad(
        const GameplayHudTextureHandle &texture,
        float x,
        float y,
        float quadWidth,
        float quadHeight) const override;
    bgfx::TextureHandle ensureHudTextureColor(
        const GameplayHudTextureHandle &texture,
        uint32_t colorAbgr) const override;
    void renderLayoutLabel(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        const std::string &label) const override;
    std::optional<GameplayHudFontHandle> findHudFont(const std::string &fontName) const override;
    float measureHudTextWidth(const GameplayHudFontHandle &font, const std::string &text) const override;
    std::vector<std::string> wrapHudTextToWidth(
        const GameplayHudFontHandle &font,
        const std::string &text,
        float maxWidth) const override;
    bgfx::TextureHandle ensureHudFontMainTextureColor(
        const GameplayHudFontHandle &font,
        uint32_t colorAbgr) const override;
    void renderHudFontLayer(
        const GameplayHudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const override;
    bool hasHudRenderResources() const override;
    void prepareHudView(int width, int height) const override;
    void submitHudQuadBatch(
        const std::vector<GameplayHudBatchQuad> &quads,
        int screenWidth,
        int screenHeight) const override;
    std::string resolvePortraitTextureName(const Character &character) const override;
    void consumePendingPortraitEventFxRequests() override;
    void renderPortraitFx(
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight) const override;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const override;
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const override;
    void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) override;
    const std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems() const override;
    void submitWorldTextureQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1) const override;
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const override;

private:
    GameplayOverlayContext createGameplayOverlayContext();
    GameplayOverlayContext createGameplayOverlayContext() const;

    GameplayOverlayInteractionState &interactionState()
    {
        return m_overlayInteractionState;
    }

    const GameplayOverlayInteractionState &interactionState() const
    {
        return m_overlayInteractionState;
    }

    EventDialogContent &activeEventDialog()
    {
        return m_gameplayUiController.eventDialog().content;
    }

    const EventDialogContent &activeEventDialog() const
    {
        return m_gameplayUiController.eventDialog().content;
    }

    size_t &eventDialogSelectionIndex()
    {
        return m_gameplayUiController.eventDialog().selectionIndex;
    }

    const size_t &eventDialogSelectionIndex() const
    {
        return m_gameplayUiController.eventDialog().selectionIndex;
    }

    std::string &statusBarEventText()
    {
        return m_gameplayUiController.statusBar().eventText;
    }

    const std::string &statusBarEventText() const
    {
        return m_gameplayUiController.statusBar().eventText;
    }

    float &statusBarEventRemainingSeconds()
    {
        return m_gameplayUiController.statusBar().eventRemainingSeconds;
    }

    const float &statusBarEventRemainingSeconds() const
    {
        return m_gameplayUiController.statusBar().eventRemainingSeconds;
    }

    GameplayUiController::HouseShopOverlayState &houseShopOverlay()
    {
        return m_gameplayUiController.houseShopOverlay();
    }

    const GameplayUiController::HouseShopOverlayState &houseShopOverlay() const
    {
        return m_gameplayUiController.houseShopOverlay();
    }

    using HudTextureHandleInternal = GameplayHudTextureData;
    using HudFontGlyphMetricsInternal = GameplayHudFontGlyphMetricsData;
    using HudFontHandleInternal = GameplayHudFontData;
    using HudFontColorTextureHandleInternal = GameplayHudFontColorTextureData;
    using HudTextureColorTextureHandleInternal = GameplayHudTextureColorTextureData;
    using HudAssetLoadCache = GameplayAssetLoadCache;

    GameplayDialogController::Context buildDialogContext(EventRuntimeState &eventRuntimeState);
    void renderDialogueOverlay(int width, int height, bool renderAboveHud);
    void renderCharacterOverlay(int width, int height, bool renderAboveHud);
    void handleSpellbookOverlayInput(const bool *pKeyboardState, int width, int height);
    void handleCharacterOverlayInput(const bool *pKeyboardState, int width, int height);
    void presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent);
    void closeActiveEventDialog();
    std::optional<std::string> findCachedAssetPath(const std::string &directoryPath, const std::string &fileName) const;
    std::optional<std::vector<uint8_t>> readCachedBinaryFile(const std::string &assetPath) const;
    std::optional<std::vector<uint8_t>> loadHudBitmapPixelsBgraCached(
        const std::string &textureName,
        int &width,
        int &height) const;
    bool loadHudTexture(const std::string &textureName);
    bool loadHudFont(const std::string &fontName);
    void clearHudResources();
    bool shouldEnableGameplayMouseLook() const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    std::optional<GameplayResolvedHudLayoutElement> resolvePartyPortraitRect(int width, int height, size_t memberIndex) const;
    std::optional<size_t> resolvePartyPortraitIndexAtPoint(int width, int height, float x, float y) const;
    void updateItemInspectOverlayState(int width, int height);
    void renderGameplayMouseLookOverlay(int width, int height) const;
    bool tryAutoPlaceHeldItemOnPartyMember(size_t memberIndex, bool showFailureStatus = true);
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const override;

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    IndoorDebugRenderer *m_pIndoorRenderer = nullptr;
    IndoorSceneRuntime *m_pIndoorSceneRuntime = nullptr;
    GameAudioSystem *m_pGameAudioSystem = nullptr;
    std::optional<MapStatsEntry> m_map;
    GameSettings m_settings = GameSettings::createDefault();
    GameSession &m_gameSession;
    GameplayUiRuntime &m_gameplayUiRuntime;
    GameplayUiController &m_gameplayUiController;
    GameplayDialogController &m_gameplayDialogController;
    GameplayOverlayInteractionState &m_overlayInteractionState;
    GameplayAssetLoadCache &m_hudAssetLoadCache;
    UiLayoutManager &m_uiLayoutManager;
    bool m_partyPortraitClickLatch = false;
    std::optional<size_t> m_partyPortraitPressedIndex;
    uint64_t m_lastPartyPortraitClickTicks = 0;
    std::optional<size_t> m_lastPartyPortraitClickedIndex;
    bool m_gameplayHudButtonClickLatch = false;
    int m_gameplayHudPressedButton = 0;
    bool m_gameplayMouseLookActive = false;
    bool m_gameplayCursorModeActive = false;
    std::vector<HudTextureHandleInternal> &m_hudTextureHandles;
    std::unordered_map<std::string, size_t> &m_hudTextureIndexByName;
    std::vector<HudFontHandleInternal> &m_hudFontHandles;
    std::vector<HudFontColorTextureHandleInternal> &m_hudFontColorTextureHandles;
    std::vector<HudTextureColorTextureHandleInternal> &m_hudTextureColorTextureHandles;
    std::unordered_map<std::string, float> &m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> &m_renderedInspectableHudItems;
    GameplayHudScreenState m_renderedInspectableHudState = GameplayHudScreenState::Gameplay;
};
} // namespace OpenYAMM::Game
