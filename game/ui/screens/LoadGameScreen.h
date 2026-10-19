#pragma once

#include "game/data/GameDataRepository.h"
#include "game/ui/MenuDesignScreen.h"
#include "game/ui/UiLayoutManager.h"

#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class LoadGameScreen : public MenuDesignScreen
{
  public:
    using LoadAction = std::function<bool(const std::filesystem::path &)>;
    using CancelAction = std::function<void()>;
    using SaveAction = std::function<bool(const std::filesystem::path &, const std::string &)>;

    LoadGameScreen(const Engine::AssetFileSystem &assetFileSystem, const GameDataRepository &gameData,
                   LoadAction loadAction, CancelAction cancelAction, bool fromGameplay = false,
                   GameAudioSystem *pAudio = nullptr, const std::string &language = "en");

    AppMode mode() const override;
    void prepareForFirstFrame();
    void onEnter() override;
    static void invalidateCachedSaveSlots();
    static std::optional<std::filesystem::path> mostRecentSave(std::string &mapFileName);
    void configureSave(SaveAction action, const std::string &location, float gameMinutes,
                       const std::vector<uint8_t> &previewBmp);
    void handleSdlEvent(const SDL_Event &event) override;

  private:
    struct SaveSlotSummary
    {
        std::filesystem::path path;
        std::string fileLabel;
        std::string locationName;
        std::string weekdayClockText;
        std::string dateText;
        std::string worldName;
        std::string savedAt;
        bool populated = false;
        int previewWidth = 0;
        int previewHeight = 0;
        std::vector<uint8_t> previewPixelsBgra;
    };

    void drawScreen(float deltaSeconds) override;
    void refreshSaveSlots();
    bool tryLoadSelectedSlot();
    void cancel();
    void loadCachedSaveSlots();

    const GameDataRepository *m_pGameData = nullptr;
    LoadAction m_loadAction;
    CancelAction m_cancelAction;
    size_t m_selectedIndex = 0;
    float m_scrollOffset = 0;
    bool m_revealSelection = false;
    uint64_t m_lastClickedSlotTicks = 0;
    size_t m_lastClickedSlotIndex = static_cast<size_t>(-1);
    std::vector<SaveSlotSummary> m_slots;
    bool m_slotsLoaded = false;
    SaveAction m_saveAction;
    std::string m_saveName;
    std::string m_currentLocation;
    std::string m_currentDate;
    std::string m_currentClock;
    std::string m_error;
    bool m_newSave = true;
    bool m_nameEditing = false;
    bool m_commitRequested = false;
    bool m_fromGameplay = false;
    int m_previewWidth = 0;
    int m_previewHeight = 0;
    std::vector<uint8_t> m_previewPixels;
    void commitSave();
    void requestLoad();
    void requestDelete();

    static std::vector<SaveSlotSummary> s_cachedSlots;
    static bool s_cachedSlotsValid;
};
} // namespace OpenYAMM::Game
