#pragma once

#include "game/app/GameSettings.h"
#include "game/tables/ChestTable.h"
#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/ui/GameplayOverlayAdapters.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/tables/HouseTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/UiLayoutManager.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameSession;
class GameAudioSystem;
class GameplayFxService;
struct GameplayInputFrame;
class GameplayItemService;
class GameplaySpellService;
class ItemTable;
class MonsterTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct HouseEntry;
struct ItemDefinition;

class GameplayScreenRuntime
{
public:
    using HudLayoutElement = UiLayoutManager::LayoutElement;
    using ResolvedHudLayoutElement = GameplayResolvedHudLayoutElement;
    using HudTextureHandle = GameplayHudTextureHandle;
    using HudFontHandle = GameplayHudFontHandle;
    using DialogueCloseCallback = std::function<void()>;
    using DialogContextBuilder =
        std::function<GameplayDialogController::Context(EventRuntimeState &eventRuntimeState)>;
    using ActiveDialogContextBuilder = DialogContextBuilder;
    using ActiveDialogActionCallback = std::function<void(const GameplayDialogController::Result &result)>;
    using PendingEventDialogPresenter = std::function<void(size_t previousMessageCount, bool allowNpcFallbackContent)>;
    using PendingEventDialogOpenedCallback =
        std::function<void(const GameplayDialogController::PresentPendingDialogResult &result)>;
    struct PreparedSaveGameRequest
    {
        std::filesystem::path path;
        std::string saveName;
    };
    struct SharedUiBootstrapConfig
    {
        const Engine::AssetFileSystem *pAssetFileSystem = nullptr;
        size_t portraitMemberCount = 0;
        bool initializeHouseVideoPlayer = false;
        bool preloadReferencedAssets = true;
    };
    struct SharedUiBootstrapResult
    {
        bool layoutsLoaded = false;
        bool portraitRuntimeLoaded = false;
        bool houseVideoPlayerInitialized = false;
    };
    using SaveGameExecutor = std::function<bool(const PreparedSaveGameRequest &request)>;

    explicit GameplayScreenRuntime(GameSession &session);

    void bindAudioSystem(GameAudioSystem *pAudioSystem);
    void bindSettings(GameSettings *pSettings);
    void bindSceneAdapter(IGameplayOverlaySceneAdapter *pSceneAdapter);
    void clearSceneAdapter(IGameplayOverlaySceneAdapter *pSceneAdapter);
    void clearTransientBindings();

    IGameplayWorldRuntime *worldRuntime() const;
    Party *party() const;
    const Party *partyReadOnly() const;
    float partyX() const;
    float partyY() const;
    float partyFootZ() const;
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
    const MonsterTable *monsterTable() const;

    GameplayUiController::CharacterScreenState &characterScreen() const;
    GameplayUiController::HeldInventoryItemState &heldInventoryItem() const;
    GameplayUiController::ItemInspectOverlayState &itemInspectOverlay() const;
    GameplayUiController::CharacterInspectOverlayState &characterInspectOverlay() const;
    GameplayUiController::BuffInspectOverlayState &buffInspectOverlay() const;
    GameplayUiController::CharacterDetailOverlayState &characterDetailOverlay() const;
    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay() const;
    GameplayUiController::SpellInspectOverlayState &spellInspectOverlay() const;
    GameplayUiController::ReadableScrollOverlayState &readableScrollOverlay() const;
    GameplayUiController::SpellbookState &spellbook() const;
    GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay() const;
    GameplayUiController::InventoryNestedOverlayState &inventoryNestedOverlay() const;
    GameplayUiController::HouseShopOverlayState &houseShopOverlay() const;
    GameplayUiController::HouseBankState &houseBankState() const;
    GameplayUiController::JournalScreenState &journalScreenState() const;
    GameplayUiController::RestScreenState &restScreenState() const;
    GameplayUiController::MenuScreenState &menuScreenState() const;
    GameplayUiController::ControlsScreenState &controlsScreenState() const;
    GameplayUiController::KeyboardScreenState &keyboardScreenState() const;
    GameplayUiController::VideoOptionsScreenState &videoOptionsScreenState() const;
    GameplayUiController::SaveGameScreenState &saveGameScreenState() const;
    GameplayUiController::LoadGameScreenState &loadGameScreenState() const;
    const GameplayUiController::CharacterScreenState &characterScreenReadOnly() const;
    const GameplayUiController::ItemInspectOverlayState &itemInspectOverlayReadOnly() const;
    const GameplayUiController::CharacterInspectOverlayState &characterInspectOverlayReadOnly() const;
    const GameplayUiController::BuffInspectOverlayState &buffInspectOverlayReadOnly() const;
    const GameplayUiController::CharacterDetailOverlayState &characterDetailOverlayReadOnly() const;
    const GameplayUiController::ActorInspectOverlayState &actorInspectOverlayReadOnly() const;
    const GameplayUiController::SpellInspectOverlayState &spellInspectOverlayReadOnly() const;
    const GameplayUiController::ReadableScrollOverlayState &readableScrollOverlayReadOnly() const;
    const GameplayUiController::SpellbookState &spellbookReadOnly() const;
    const GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlayReadOnly() const;
    const GameplayUiController::JournalScreenState &journalScreenStateReadOnly() const;
    const JournalQuestTable *journalQuestTable() const;
    const JournalHistoryTable *journalHistoryTable() const;
    const JournalAutonoteTable *journalAutonoteTable() const;
    const std::string &currentMapFileName() const;
    float gameplayCameraYawRadians() const;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const;
    EventDialogContent &activeEventDialog() const;
    std::string &statusBarEventText() const;
    float &statusBarEventRemainingSeconds() const;
    const std::string &statusBarHoverText() const;
    std::string &mutableStatusBarHoverText() const;
    size_t &eventDialogSelectionIndex() const;
    GameplayOverlayInteractionState &interactionState() const;
    const GameplayInputFrame *currentGameplayInputFrame() const;

    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady);
    size_t selectedCharacterScreenSourceIndex() const;
    const Character *selectedCharacterScreenCharacter() const;
    bool isAdventurersInnCharacterSourceActive() const;
    bool isAdventurersInnScreenActive() const;
    bool isReadOnlyAdventurersInnCharacterViewActive() const;
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void openRestOverlay();
    void beginRestAction(GameplayUiController::RestMode mode, float minutes, bool consumeFood);
    void startRestAction(GameplayUiController::RestMode mode, float minutes);
    void startInnRest(float durationMinutes);
    void openSpellbookOverlay();
    void openChestTransferInventoryOverlay();
    void toggleCharacterInventoryScreen();
    uint32_t closeActiveEventDialog();
    void handleDialogueCloseRequest();
    void closeRestOverlay();
    void completeRestAction(bool closeRestScreenAfterCompletion);
    void openMenuOverlay();
    void closeMenuOverlay();
    void openControlsOverlay();
    void closeControlsOverlay();
    void openKeyboardOverlay();
    void closeKeyboardOverlayToControls();
    void closeKeyboardOverlayToMenu();
    void openVideoOptionsOverlay();
    void closeVideoOptionsOverlay();
    void openSaveGameOverlay();
    void refreshSaveGameOverlaySlots();
    void closeSaveGameOverlay();
    void requestOpenNewGameScreen();
    void requestOpenLoadGameScreen();
    void openJournalOverlay();
    void closeJournalOverlay();
    void closeHouseShopOverlay();
    void ensurePendingEventDialogPresented(bool allowNpcFallbackContent = true);
    void ensurePendingEventDialogPresented(
        bool allowNpcFallbackContent,
        const DialogContextBuilder &contextBuilder,
        const PendingEventDialogOpenedCallback &onOpened = {});
    void presentPendingEventDialog(
        size_t previousMessageCount,
        bool allowNpcFallbackContent,
        const DialogContextBuilder &contextBuilder = {},
        const PendingEventDialogOpenedCallback &onOpened = {});
    void closeActiveDialogActionResult(
        const GameplayDialogController::Result &result,
        const DialogueCloseCallback &closeActiveDialog = {});
    void presentPendingDialogActionResult(
        const GameplayDialogController::Result &result,
        const PendingEventDialogPresenter &presentPendingEventDialogCallback = {});
    void executeActiveDialogAction();
    void executeActiveDialogAction(
        const ActiveDialogContextBuilder &contextBuilder,
        const ActiveDialogActionCallback &beforeCloseContinuation = {},
        const DialogueCloseCallback &closeActiveDialog = {},
        const ActiveDialogActionCallback &afterCloseContinuation = {},
        const PendingEventDialogPresenter &presentPendingEventDialogCallback = {});
    void refreshHouseBankInputDialog();
    void confirmHouseBankInput();
    void closeInventoryNestedOverlay();
    void closeSpellbookOverlay(const std::string &statusText = "");
    void openUtilitySpellOverlay(
        GameplayUiController::UtilitySpellOverlayMode mode,
        uint32_t spellId,
        size_t casterMemberIndex,
        bool lloydRecallMode = false);
    void closeUtilitySpellOverlayAfterSpellResolution(uint32_t spellId);
    bool tryAutoPlaceHeldInventoryItemOnPartyMember(size_t memberIndex, bool showFailureStatus);
    GameplayItemService &itemService() const;
    GameplayFxService &fxService() const;
    GameplaySpellService &spellService() const;
    void resetDialogueOverlayInteractionState();
    void resetSpellbookOverlayInteractionState();
    void resetCharacterOverlayInteractionState();
    void updatePartyPortraitAnimations(float deltaSeconds);
    uint32_t animationTicks() const;
    void triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId);
    void triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId animationId);
    bool canPlaySpeechReaction(size_t memberIndex, SpeechId speechId, uint32_t nowTicks);
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation);
    void queueDelayedSpeechReaction(size_t memberIndex, SpeechId speechId, float delaySeconds);
    void updateDelayedSpeechReactions(float deltaSeconds);
    void playHouseSound(uint32_t soundId);
    void playCommonUiSound(SoundId soundId);
    void stopAllAudioPlayback();
    void consumePendingPartyAudioRequests();
    void consumePendingEventRuntimeAudioRequests();
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName);
    bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName);
    void triggerSpellFailureFeedback(size_t casterMemberIndex, const std::string &statusText);
    void resetUtilitySpellOverlayInteractionState();
    void resetInventoryNestedOverlayInteractionState();
    void resetLootOverlayInteractionState();
    GameSettings &mutableSettings() const;
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;
    void updatePreviousKeyboardStateSnapshot(const bool *pKeyboardState);
    void commitSettingsChange();
    std::optional<PreparedSaveGameRequest> prepareSelectedSaveGameRequest() const;
    bool trySaveToSelectedGameSlot(const SaveGameExecutor &executor);
    bool trySaveToSelectedGameSlot();
    int restFoodRequired() const;
    const GameSettings &settingsSnapshot() const;
    GameplayUiRuntime &gameplayUiRuntime() const;
    SharedUiBootstrapResult initializeSharedUiRuntime(const SharedUiBootstrapConfig &config);
    void bindAssetFileSystem(const Engine::AssetFileSystem *pAssetFileSystem);
    void clearUiControllerRuntimeState();
    bool ensureGameplayLayoutsLoaded();
    void preloadReferencedAssets();
    bool ensurePortraitRuntimeLoaded();
    void resetPortraitFxStates(size_t memberCount);
    void resetOverlayInteractionState();
    bool initializeHouseVideoPlayer();
    void shutdownHouseVideoPlayer();
    void stopHouseVideoPlayback();
    bool playHouseVideo(const std::string &videoStem);
    bool playHouseVideo(const std::string &videoStem, const std::string &videoDirectory);
    void queueBackgroundHouseVideoPreload(const std::string &videoStem);
    void updateHouseVideoBackgroundPreloads();
    void updateHouseVideoPlayback(float deltaSeconds);
    bool isControlsRenderButtonPressed(GameplayControlsRenderButton button) const;
    bool isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const;
    void clearHudLayoutRuntimeHeightOverrides();
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height);

    const HouseEntry *findHouseEntry(uint32_t houseId) const;
    const HudLayoutElement *findHudLayoutElement(const std::string &layoutId) const;
    int defaultHudLayoutZIndexForScreen(const std::string &screen) const;
    GameplayHudScreenState currentHudScreenState() const;
    std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const;

    std::optional<ResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const;
    std::optional<ResolvedHudLayoutElement> resolvePartyPortraitRect(int width, int height, size_t memberIndex) const;
    std::optional<size_t> resolvePartyPortraitIndexAtPoint(int width, int height, float x, float y) const;
    std::optional<ResolvedHudLayoutElement> resolveChestGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveInventoryNestedOverlayGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveHouseShopOverlayFrame(int width, int height) const;
    bool isPointerInsideResolvedElement(
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY) const;
    const std::string *resolveInteractiveAssetName(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed) const;
    void submitHudTexturedQuad(
        const HudTextureHandle &texture,
        float x,
        float y,
        float quadWidth,
        float quadHeight) const;
    void renderLayoutLabel(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        const std::string &label) const;
    std::optional<HudFontHandle> findHudFont(const std::string &fontName) const;
    float measureHudTextWidth(const HudFontHandle &font, const std::string &text) const;
    std::vector<std::string> wrapHudTextToWidth(
        const HudFontHandle &font,
        const std::string &text,
        float maxWidth) const;
    bgfx::TextureHandle ensureHudFontMainTextureColor(const HudFontHandle &font, uint32_t colorAbgr) const;
    void renderHudFontLayer(
        const HudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;
    void bindHudRenderBackend(const GameplayHudRenderBackend &backend);
    void clearHudRenderBackend();
    void releaseHudGpuResources(bool destroyBgfxResources);
    void clearSharedUiRuntime();
    bool hasHudRenderResources() const;
    void prepareHudView(int width, int height) const;
    void submitHudQuadBatch(
        const std::vector<GameplayHudBatchQuad> &quads,
        int screenWidth,
        int screenHeight) const;
    void renderViewportSidePanels(
        int screenWidth,
        int screenHeight,
        const std::string &textureName);
    std::string resolvePortraitTextureName(const Character &character) const;
    void renderPortraitFx(
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight) const;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const;
    float gameplayMinimapZoomScale() const;
    void zoomGameplayMinimapIn();
    void zoomGameplayMinimapOut();
    void collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines);
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const;
    bool ensureTownPortalDestinationsLoaded();
    const std::vector<GameplayTownPortalDestination> &townPortalDestinations() const;
    std::string resolveMapLocationName(const std::string &mapFileName) const;
    float measureHudTextWidth(const std::string &fontName, const std::string &text) const;
    int hudFontHeight(const std::string &fontName) const;
    std::vector<std::string> wrapHudTextToWidth(
        const std::string &fontName,
        const std::string &text,
        float maxWidth) const;
    void renderHudTextLine(
        const std::string &fontName,
        uint32_t colorAbgr,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;

    void resetHudTransientState() const;
    void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) const;
    const std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems() const;
    void beginRenderedInspectableHudFrame() const;
    GameplayHudScreenState renderedInspectableHudScreenState() const;
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const;
    const PortraitFxEventEntry *findPortraitFxEvent(PortraitFxEventKind kind) const;
    uint32_t defaultPortraitAnimationLengthTicks(PortraitId portraitId) const;
    std::string resolveEquippedItemHudTextureName(
        const ItemDefinition &itemDefinition,
        uint32_t dollTypeId,
        bool hasRightHandWeapon,
        EquipmentSlot slot);
    std::optional<GameplayResolvedHudLayoutElement> resolveCharacterEquipmentRenderRect(
        const UiLayoutManager::LayoutElement &layout,
        const ItemDefinition &itemDefinition,
        const GameplayHudTextureHandle &texture,
        const CharacterDollTypeEntry *pCharacterDollType,
        EquipmentSlot slot,
        int screenWidth,
        int screenHeight) const;
    void submitWorldTextureQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1) const;
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const;

private:
    struct DelayedSpeechReaction
    {
        size_t memberIndex = 0;
        SpeechId speechId = SpeechId::None;
        float remainingSeconds = 0.0f;
    };

    IGameplayOverlaySceneAdapter &sceneAdapter() const;
    GameplayUiController &uiController() const;
    GameplayUiRuntime &uiRuntime() const;
    GameplayDialogUiFlowState dialogUiFlowState();
    void updatePortraitAnimation(Character &member, size_t memberIndex, uint32_t deltaTicks);
    void playPortraitExpression(size_t memberIndex, PortraitId portraitId, std::optional<uint32_t> durationTicks);
    GameplayDialogController::Context buildDialogContext(EventRuntimeState &eventRuntimeState);
    void returnToHouseBankMainDialogShared();

    GameSession &m_session;
    GameAudioSystem *m_pAudioSystem = nullptr;
    GameSettings *m_pSettings = nullptr;
    IGameplayOverlaySceneAdapter *m_pSceneAdapter = nullptr;
    std::optional<DelayedSpeechReaction> m_delayedSpeechReaction;
    uint64_t m_lastSpellFailSoundTicks = 0;
    mutable std::optional<std::string> m_resolvedInteractiveAssetName;
    mutable IGameplayWorldRuntime *m_pCachedMinimapWorldRuntime = nullptr;
    mutable uint32_t m_cachedMinimapLineMilliseconds = 0;
    mutable uint32_t m_cachedMinimapMarkerMilliseconds = 0;
    mutable bool m_cachedMinimapLinesValid = false;
    mutable bool m_cachedMinimapMarkersValid = false;
    mutable std::vector<GameplayMinimapLineState> m_cachedMinimapLines;
    mutable std::vector<GameplayMinimapMarkerState> m_cachedMinimapMarkers;
};
} // namespace OpenYAMM::Game
