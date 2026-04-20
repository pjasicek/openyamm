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
    void triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId) override;
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
private:
    GameplayOverlayContext createGameplayOverlayContext();
    GameplayOverlayContext createGameplayOverlayContext() const;
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
    bool shouldEnableGameplayMouseLook() const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    void updateItemInspectOverlayState(int width, int height);

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
    bool m_gameplayMouseLookActive = false;
    bool m_gameplayCursorModeActive = false;
};
} // namespace OpenYAMM::Game
