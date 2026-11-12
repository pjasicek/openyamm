#pragma once

#include "game/data/GameDataRepository.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/ui/MenuDesignScreen.h"
#include "game/ui/UiLayoutManager.h"

#include <filesystem>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
// What saving costs in food here (MAW from Nightmare): now, with enemies near, and what the party carries.
struct SaveFoodCost
{
    int food = 0;
    int foodWithEnemiesNear = 0;
    int carried = 0;
};

// The Load and Save screens. The saves are listed under the playthrough each belongs to (a party's own game, from
// its statistics id), the playthroughs by last play with the one being played first. A playthrough's heading folds
// its saves and, selected, shows its facts, a name the player may give it and its deletion. The Save screen lists the
// playthrough being played until "All" is chosen.
class LoadGameScreen : public MenuDesignScreen
{
  public:
    using LoadAction = std::function<bool(const std::filesystem::path &)>;
    using CancelAction = std::function<void()>;
    using SaveAction = std::function<bool(const std::filesystem::path &, const std::string &)>;
    using SortOrderAction = std::function<void(bool newestFirst)>;

    // loadWarning: what loading from play costs now, said in the confirmation (MAW's pending Beyond Madness death).
    LoadGameScreen(const Engine::AssetFileSystem &assetFileSystem, const GameDataRepository &gameData,
                   LoadAction loadAction, CancelAction cancelAction, bool fromGameplay = false,
                   GameAudioSystem *pAudio = nullptr, std::string loadWarning = {});

    AppMode mode() const override;
    // The layout, and the saves folder's first read on a worker thread (startSaveScan).
    void prepareForFirstFrame();
    void onEnter() override;
    // Reads the saves folder on a worker thread, so the list is ready when a Load or Save screen opens.
    static void startSaveScan();
    // Ends a scan still running at its current save, and forgets the saves read.
    static void stopSaveScan();
    static std::optional<std::filesystem::path> mostRecentSave(std::string &mapFileName);
    void configureSave(SaveAction action, const std::string &location, float gameMinutes,
                       const std::vector<uint8_t> &previewBmp, SaveFoodCost foodCost = {});
    // The playthrough being played (screens opened from play), its real time played in all (reloaded stretches too)
    // and the part of it a save made now would hold.
    void configureCurrentPlaythrough(const std::string &playthroughId, double playedSeconds, double saveSeconds);
    // The list order (gameplay.save_list_order) and where a change of it is remembered.
    void configureSortOrder(bool newestFirst, SortOrderAction changed);
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
        std::string rulesetId;
        // "MAW" and "Nightmare"; "Standard" and nothing for the Standard ruleset.
        std::string rulesetName;
        std::string difficultyName;
        // "MAW · Hell difficulty · Horizontal progression"; empty for the Standard ruleset.
        std::string rulesetBadge;
        // Empty: a save that names no playthrough.
        std::string playthroughId;
        // "6 h 05 min", or "-" for a save from before the statistics.
        std::string playedText;
        std::string savedAt;
        std::filesystem::file_time_type modified = {};
        bool populated = false;
        int previewWidth = 0;
        int previewHeight = 0;
        std::vector<uint8_t> previewPixelsBgra;
    };

    // A playthrough's saves under one heading.
    struct PlaythroughGroup
    {
        std::string id;
        // The player's name for it, else the automatic one ("Enroth · MAW Nightmare").
        std::string name;
        std::string automaticName;
        std::string rules;
        std::string difficulty;
        std::string startedIn;
        std::string started;
        std::string lastPlayed;
        std::string played;
        // Its saves in the list's order, as indices into m_slots, and the newest of them.
        std::vector<size_t> slots;
        size_t newestSlot = 0;
        bool hasStatistics = false;
    };

    enum class Selection : uint8_t
    {
        None,
        NewSave,
        Slot,
        Group,
    };

    enum class RowKind : uint8_t
    {
        NewSave,
        Group,
        Slot,
    };

    // A row of the list; index is the group's in m_groups or the slot's in m_slots.
    struct ListRow
    {
        RowKind kind = RowKind::NewSave;
        size_t index = 0;
    };

    enum class TextEdit : uint8_t
    {
        None,
        SaveName,
        PlaythroughName,
    };

    void drawScreen(float deltaSeconds) override;
    // The Save screen's "This playthrough" / "All" / one ruleset switch, and whether it changed.
    bool drawScopeButtons(const std::string &prefix);
    // The Load screen's ruleset filter (All, then one per ruleset the saves were played with), and whether it changed.
    bool drawRulesetFilters(const std::string &prefix);
    // The Name / Newest switch, and whether the order changed.
    bool drawSortButtons(const std::string &prefix);
    // A playthrough's heading in the list, and whether it was activated.
    bool drawGroupRow(const std::string &id, const Rect &rect, const PlaythroughGroup &group, bool selected);
    void drawSaveDetails(const std::string &prefix, const SaveSlotSummary *pSlot, bool saveAffordable);
    void drawPlaythroughDetails(const PlaythroughGroup &group);
    // Orders m_slots by the switch and groups them again.
    void sortSlots();
    void rebuildGroups();
    void describeGroup(PlaythroughGroup &group);
    std::vector<ListRow> listRows() const;
    std::optional<size_t> selectedRow(const std::vector<ListRow> &rows) const;
    void selectRow(const ListRow &row);
    void selectDefaultRow(const std::vector<ListRow> &rows);
    void activateRow(const ListRow &row);
    const PlaythroughGroup *findGroup(const std::string &playthroughId) const;
    // "MAW", or "Standard", in the interface language.
    const std::string &rulesetDisplayName(const std::string &rulesetId);
    std::string continentNameOfWorld(const std::string &worldId) const;
    Rect playthroughNameField() const;
    void finishTextEdit();
    void commitPlaythroughName();
    // The list from the saves read so far, reading only those that are new or changed.
    void refreshSaveSlots();
    bool tryLoadSelectedSlot();
    void cancel();

    const GameDataRepository *m_pGameData = nullptr;
    LoadAction m_loadAction;
    CancelAction m_cancelAction;
    Selection m_selection = Selection::None;
    // The selected slot (Selection::Slot) and playthrough (Selection::Group).
    size_t m_selectedIndex = 0;
    std::string m_selectedGroupId;
    float m_scrollOffset = 0;
    bool m_revealSelection = false;
    uint64_t m_lastClickedSlotTicks = 0;
    size_t m_lastClickedSlotIndex = static_cast<size_t>(-1);
    std::vector<SaveSlotSummary> m_slots;
    std::vector<PlaythroughGroup> m_groups;
    // The unfolded playthroughs; the first of the list unfolds when the screen has chosen none yet.
    std::unordered_set<std::string> m_expandedGroups;
    bool m_expansionChosen = false;
    std::unordered_map<std::string, PlaythroughStatistics::StoredSummary> m_playthroughRecords;
    std::unordered_map<std::string, std::string> m_playthroughNames;
    std::unordered_map<std::string, std::string> m_rulesetNames;
    std::string m_currentPlaythroughId;
    double m_currentPlayedSeconds = 0.0;
    double m_currentSaveSeconds = 0.0;
    // The Save screen lists every playthrough, not only the one being played.
    bool m_showAllPlaythroughs = false;
    // The rulesets the saves were played with, Standard first; the filter is one of them, empty for all. The Save
    // screen sets it together with m_showAllPlaythroughs.
    std::vector<std::string> m_rulesetFilters;
    std::string m_rulesetFilter;
    bool m_newestFirst = false;
    SortOrderAction m_sortOrderChanged;
    size_t m_newerSaveCount = 0;
    bool m_slotsLoaded = false;
    uint64_t m_slotsSignature = 0;
    SaveAction m_saveAction;
    std::string m_saveName;
    std::string m_currentLocation;
    std::string m_currentDate;
    std::string m_currentClock;
    std::string m_error;
    SaveFoodCost m_foodCost;
    TextEdit m_textEdit = TextEdit::None;
    // The playthrough being renamed and its name as typed so far.
    std::string m_editedGroupId;
    std::string m_playthroughName;
    bool m_commitRequested = false;
    bool m_fromGameplay = false;
    std::string m_loadWarning;
    int m_previewWidth = 0;
    int m_previewHeight = 0;
    std::vector<uint8_t> m_previewPixels;
    void commitSave();
    void requestLoad();
    void requestDelete();
    void requestDeletePlaythrough();
    void requestImportSaves();
    void finishImportSaves();

    // The folder picker may answer on another thread; the screen polls it while drawing.
    struct FolderPick
    {
        std::mutex mutex;
        bool finished = false;
        std::optional<std::filesystem::path> folder;
    };
    std::shared_ptr<FolderPick> m_folderPick;
};
} // namespace OpenYAMM::Game
