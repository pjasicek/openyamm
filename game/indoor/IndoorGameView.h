#pragma once

#include "engine/AssetFileSystem.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
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
#include "game/ui/GameplayOverlayAdapters.h"
#include "game/ui/UiLayoutManager.h"

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
struct GameplayInputFrame;
struct ArcomageLibrary;
class IndoorRenderer;
class IndoorPartyRuntime;
class IndoorSceneRuntime;
class GameplayScreenRuntime;

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
        IndoorRenderer &indoorRenderer,
        IndoorSceneRuntime &sceneRuntime,
        GameAudioSystem *pGameAudioSystem);
    void setSettingsSnapshot(const GameSettings &settings);
    void render(int width, int height, const GameplayInputFrame &input, float deltaSeconds);
    void shutdown();
    void reopenMenuScreen();
    bool requestQuickSave();

    IndoorPartyRuntime *partyRuntime() const;
    IGameplayWorldRuntime *worldRuntime() const;
    GameAudioSystem *audioSystem() const;
    float gameplayCameraYawRadians() const override;
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void executeActiveDialogAction() override;
    bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) override;
    GameSettings &mutableSettings();
    bool trySaveToSelectedGameSlot() override;
    const GameSettings &settingsSnapshot() const;
    GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const;
private:
    GameplayDialogController::Context buildDialogContext(EventRuntimeState &eventRuntimeState);
    void presentPendingEventFeedback();
    std::optional<std::string> findCachedAssetPath(const std::string &directoryPath, const std::string &fileName) const;
    std::optional<std::vector<uint8_t>> readCachedBinaryFile(const std::string &assetPath) const;
    void syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled);
    void updateItemInspectOverlayState(int width, int height, const GameplayInputFrame &input);
    void updateActorInspectOverlayState(int width, int height, const GameplayInputFrame &input);
    void updateFootstepAudio(float deltaSeconds);
    void updateDialogueVideoPlayback(float deltaSeconds);
    bool beginSaveWithPreview(
        const std::filesystem::path &path,
        const std::string &saveName,
        bool closeUiOnSuccess);

    struct PendingSavePreviewCaptureState
    {
        bool active = false;
        bool screenshotRequested = false;
        std::filesystem::path savePath;
        std::string requestId;
        std::string saveName;
        bool closeUiOnSuccess = false;
        uint64_t startedTicks = 0;
    };

    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    IndoorRenderer *m_pIndoorRenderer = nullptr;
    IndoorSceneRuntime *m_pIndoorSceneRuntime = nullptr;
    GameAudioSystem *m_pGameAudioSystem = nullptr;
    std::optional<MapStatsEntry> m_map;
    GameSettings m_settings = GameSettings::createDefault();
    GameSession &m_gameSession;
    int m_lastRenderWidth = 0;
    int m_lastRenderHeight = 0;
    bool m_renderGameplayUiThisFrame = true;
    bool m_dumpGameplayStateLatch = false;
    PendingSavePreviewCaptureState m_pendingSavePreviewCapture = {};
    bool m_hasLastFootstepPosition = false;
    float m_lastFootstepX = 0.0f;
    float m_lastFootstepY = 0.0f;
    float m_walkingMotionHoldSeconds = 0.0f;
    std::optional<uint32_t> m_activeWalkingSoundId;
};
} // namespace OpenYAMM::Game
