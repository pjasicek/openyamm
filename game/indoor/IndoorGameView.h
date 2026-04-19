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
#include "game/ui/IGameplayOverlayView.h"
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
struct ArcomageLibrary;
class IndoorDebugRenderer;
class IndoorPartyRuntime;
class IndoorSceneRuntime;

using IndoorSpellbookPointerTargetType = GameplaySpellbookPointerTargetType;
using IndoorSpellbookPointerTarget = GameplaySpellbookPointerTarget;
using IndoorCharacterPointerTargetType = GameplayCharacterPointerTargetType;
using IndoorCharacterPointerTarget = GameplayCharacterPointerTarget;

class IndoorGameView : public IGameplayOverlayView
{
public:
    IndoorGameView(
        GameplayUiController &gameplayUiController,
        GameplayDialogController &gameplayDialogController,
        GameplayOverlayInteractionState &overlayInteractionState);

    bool initialize(
        const Engine::AssetFileSystem &assetFileSystem,
        const MapStatsEntry &map,
        const std::vector<MapStatsEntry> &mapEntries,
        IndoorDebugRenderer &indoorRenderer,
        IndoorSceneRuntime &sceneRuntime,
        const ChestTable &chestTable,
        const HouseTable &houseTable,
        const ClassSkillTable &classSkillTable,
        const CharacterDollTable &characterDollTable,
        const CharacterInspectTable &characterInspectTable,
        const NpcDialogTable &npcDialogTable,
        const RosterTable &rosterTable,
        const ArcomageLibrary &arcomageLibrary,
        const JournalQuestTable &journalQuestTable,
        const JournalHistoryTable &journalHistoryTable,
        const JournalAutonoteTable &journalAutonoteTable,
        const ItemTable &itemTable,
        const ReadableScrollTable &readableScrollTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ItemEquipPosTable &itemEquipPosTable,
        const SpellTable &spellTable,
        GameAudioSystem *pGameAudioSystem,
        std::function<bool(
            const std::filesystem::path &,
            const std::string &,
            const std::vector<uint8_t> &,
            std::string &)> saveGameToPathCallback,
        std::function<void(const GameSettings &)> settingsChangedCallback);
    void setSettingsSnapshot(const GameSettings &settings);
    void render(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    void reopenMenuScreen();
    bool consumePendingOpenNewGameScreenRequest();
    bool consumePendingOpenLoadGameScreenRequest();

    IndoorPartyRuntime *partyRuntime() const;
    IGameplayWorldRuntime *worldRuntime() const override;
    GameAudioSystem *audioSystem() const override;
    const ItemTable *itemTable() const override;
    const StandardItemEnchantTable *standardItemEnchantTable() const override;
    const SpecialItemEnchantTable *specialItemEnchantTable() const override;
    const ClassSkillTable *classSkillTable() const override;
    const CharacterDollTable *characterDollTable() const override;
    const CharacterInspectTable *characterInspectTable() const override;
    const RosterTable *rosterTable() const override;
    const ReadableScrollTable *readableScrollTable() const override;
    const ItemEquipPosTable *itemEquipPosTable() const override;
    const SpellTable *spellTable() const override;
    const std::optional<HouseTable> &houseTable() const override;
    const std::optional<ChestTable> &chestTable() const override;
    const std::optional<NpcDialogTable> &npcDialogTable() const override;
    GameplayUiController &uiController() override;
    const GameplayUiController &uiController() const override;
    GameplayOverlayInteractionState &overlayInteractionState() override;
    const GameplayOverlayInteractionState &overlayInteractionState() const override;
    const JournalQuestTable *journalQuestTable() const override;
    const JournalHistoryTable *journalHistoryTable() const override;
    const JournalAutonoteTable *journalAutonoteTable() const override;
    const std::string &currentMapFileName() const override;
    float gameplayCameraYawRadians() const override;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override;
    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady) override;
    bool activeMemberKnowsSpell(uint32_t spellId) const override;
    bool activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const override;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f) override;
    void handleDialogueCloseRequest() override;
    void closeRestOverlay() override;
    void openMenuOverlay() override;
    void closeMenuOverlay() override;
    void openControlsOverlay() override;
    void closeControlsOverlay() override;
    void openKeyboardOverlay() override;
    void closeKeyboardOverlayToControls() override;
    void closeKeyboardOverlayToMenu() override;
    void openVideoOptionsOverlay() override;
    void closeVideoOptionsOverlay() override;
    void openSaveGameOverlay() override;
    void closeSaveGameOverlay() override;
    void requestOpenNewGameScreen() override;
    void requestOpenLoadGameScreen() override;
    void openJournalOverlay() override;
    void closeJournalOverlay() override;
    void executeActiveDialogAction() override;
    void refreshHouseBankInputDialog() override;
    void confirmHouseBankInput() override;
    void closeInventoryNestedOverlay() override;
    void closeSpellbookOverlay(const std::string &statusText = "") override;
    bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) override;
    void updateReadableScrollOverlayForHeldItem(
        size_t memberIndex,
        const GameplayCharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed) override;
    void closeReadableScrollOverlay() override;
    void resetInventoryNestedOverlayInteractionState() override;
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation) override;
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) override;
    bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) override;
    GameSettings &mutableSettings() override;
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const override;
    void commitSettingsChange() override;
    bool trySaveToSelectedGameSlot() override;
    int restFoodRequired() const override;
    const GameSettings &settingsSnapshot() const override;
    bool isControlsRenderButtonPressed(GameplayControlsRenderButton button) const override;
    bool isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const override;
    void clearHudLayoutRuntimeHeightOverrides() override;
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height) override;
    const HouseEntry *findHouseEntry(uint32_t houseId) const override;
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
    const ItemTable *m_pItemTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const CharacterInspectTable *m_pCharacterInspectTable = nullptr;
    const RosterTable *m_pRosterTable = nullptr;
    const ArcomageLibrary *m_pArcomageLibrary = nullptr;
    const JournalQuestTable *m_pJournalQuestTable = nullptr;
    const JournalHistoryTable *m_pJournalHistoryTable = nullptr;
    const JournalAutonoteTable *m_pJournalAutonoteTable = nullptr;
    const ReadableScrollTable *m_pReadableScrollTable = nullptr;
    const ItemEquipPosTable *m_pItemEquipPosTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const std::vector<MapStatsEntry> *m_pMapEntries = nullptr;
    std::optional<MapStatsEntry> m_map;
    GameSettings m_settings = GameSettings::createDefault();
    std::optional<HouseTable> m_houseTable;
    std::optional<ChestTable> m_chestTable;
    std::optional<NpcDialogTable> m_npcDialogTable;
    UiLayoutManager m_uiLayoutManager;
    GameplayUiController &m_gameplayUiController;
    GameplayDialogController &m_gameplayDialogController;
    GameplayOverlayInteractionState &m_overlayInteractionState;
    std::function<bool(
        const std::filesystem::path &,
        const std::string &,
        const std::vector<uint8_t> &,
        std::string &)> m_saveGameToPathCallback;
    std::function<void(const GameSettings &)> m_settingsChangedCallback;
    std::array<uint8_t, SDL_SCANCODE_COUNT> m_previousKeyboardState = {};
    bool &m_closeOverlayLatch;
    bool &m_restClickLatch;
    GameplayRestPointerTarget &m_restPressedTarget;
    bool &m_menuToggleLatch;
    bool &m_menuClickLatch;
    GameplayMenuPointerTarget &m_menuPressedTarget;
    bool &m_controlsToggleLatch;
    bool &m_controlsClickLatch;
    GameplayControlsPointerTarget &m_controlsPressedTarget;
    bool &m_controlsSliderDragActive;
    GameplayControlsPointerTargetType &m_controlsDraggedSlider;
    bool &m_keyboardToggleLatch;
    bool &m_keyboardClickLatch;
    GameplayKeyboardPointerTarget &m_keyboardPressedTarget;
    bool &m_videoOptionsToggleLatch;
    bool &m_videoOptionsClickLatch;
    GameplayVideoOptionsPointerTarget &m_videoOptionsPressedTarget;
    bool &m_saveGameToggleLatch;
    bool &m_saveGameClickLatch;
    GameplaySaveLoadPointerTarget &m_saveGamePressedTarget;
    std::array<bool, 39> &m_saveGameEditKeyLatches;
    bool &m_saveGameEditBackspaceLatch;
    uint64_t &m_lastSaveGameSlotClickTicks;
    std::optional<size_t> &m_lastSaveGameClickedSlotIndex;
    bool &m_journalToggleLatch;
    bool &m_journalClickLatch;
    GameplayJournalPointerTarget &m_journalPressedTarget;
    bool &m_journalMapKeyZoomLatch;
    bool &m_dialogueClickLatch;
    GameplayDialoguePointerTarget &m_dialoguePressedTarget;
    bool &m_houseShopClickLatch;
    size_t &m_houseShopPressedSlotIndex;
    bool &m_chestClickLatch;
    bool &m_chestItemClickLatch;
    GameplayChestPointerTarget &m_chestPressedTarget;
    bool &m_inventoryNestedOverlayItemClickLatch;
    std::array<bool, 10> &m_houseBankDigitLatches;
    bool &m_houseBankBackspaceLatch;
    bool &m_houseBankConfirmLatch;
    bool &m_lootChestItemLatch;
    bool &m_chestSelectUpLatch;
    bool &m_chestSelectDownLatch;
    bool &m_eventDialogSelectUpLatch;
    bool &m_eventDialogSelectDownLatch;
    bool &m_eventDialogAcceptLatch;
    std::array<bool, 5> &m_eventDialogPartySelectLatches;
    bool &m_activateInspectLatch;
    size_t &m_chestSelectionIndex;
    bool m_spellbookToggleLatch = false;
    bool &m_spellbookClickLatch;
    IndoorSpellbookPointerTarget &m_spellbookPressedTarget;
    uint64_t &m_lastSpellbookSpellClickTicks;
    uint32_t &m_lastSpellbookClickedSpellId;
    bool m_inventoryScreenToggleLatch = false;
    bool &m_characterMemberCycleLatch;
    bool m_partyPortraitClickLatch = false;
    std::optional<size_t> m_partyPortraitPressedIndex;
    uint64_t m_lastPartyPortraitClickTicks = 0;
    std::optional<size_t> m_lastPartyPortraitClickedIndex;
    std::optional<size_t> &m_pendingCharacterDismissMemberIndex;
    uint64_t &m_pendingCharacterDismissExpiresTicks;
    bool &m_characterClickLatch;
    IndoorCharacterPointerTarget &m_characterPressedTarget;
    bool m_gameplayHudButtonClickLatch = false;
    int m_gameplayHudPressedButton = 0;
    bool m_gameplayMouseLookActive = false;
    bool m_gameplayCursorModeActive = false;
    bool m_pendingOpenNewGameScreen = false;
    bool m_pendingOpenLoadGameScreen = false;
    mutable HudAssetLoadCache m_hudAssetLoadCache;
    std::vector<HudTextureHandleInternal> m_hudTextureHandles;
    std::unordered_map<std::string, size_t> m_hudTextureIndexByName;
    std::vector<HudFontHandleInternal> m_hudFontHandles;
    mutable std::vector<HudFontColorTextureHandleInternal> m_hudFontColorTextureHandles;
    mutable std::vector<HudTextureColorTextureHandleInternal> m_hudTextureColorTextureHandles;
    mutable std::unordered_map<std::string, float> m_hudLayoutRuntimeHeightOverrides;
    std::vector<GameplayRenderedInspectableHudItem> m_renderedInspectableHudItems;
    GameplayHudScreenState m_renderedInspectableHudState = GameplayHudScreenState::Gameplay;
};
} // namespace OpenYAMM::Game
