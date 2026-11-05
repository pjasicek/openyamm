#pragma once

#include "game/app/GameSettings.h"
#include "game/content/RulesetDefinition.h"
#include "game/rules/LootFilter.h"
#include "game/ui/MenuDesignScreen.h"

#include <filesystem>
#include <functional>

namespace OpenYAMM::Game
{
class GameAudioSystem;
class GameDataRepository;
class GameUpdater;

class MainMenuScreen : public MenuDesignScreen
{
  public:
    using Action = std::function<void()>;
    struct Actions
    {
        Action newGame, loadGame, saveGame, quit, resume, mainMenu;
        std::function<bool(const std::filesystem::path &)> continueGame;
        std::function<bool(const GameSettings &, bool, std::string &)> applySettings;
        // Changes the options of the game in progress (the pause menu's Rules tab).
        std::function<bool(const RulesetOptions &, std::string &)> applyRuleset;
    };
    // The ruleset of the game in progress; the pause menu of a game with a ruleset shows it in a Rules tab.
    struct CurrentGame
    {
        RulesetSelection selection;
        RulesetDefinition definition;
        // The drops the loot filter saw this session, to try a preset on (ItemRules::recentLootDrops).
        std::deque<RecentLootDrop> recentLootDrops;
    };
    MainMenuScreen(const Engine::AssetFileSystem &assets, const GameDataRepository &gameData, GameAudioSystem *pAudio,
                   const GameSettings &settings, Actions actions, std::string &settingsSection, bool paused = false,
                   std::string location = {}, std::string date = {}, GameUpdater *pUpdater = nullptr,
                   std::optional<CurrentGame> currentGame = std::nullopt);
    AppMode mode() const override;
    void prepareForFirstFrame();
    void onExit() override;
    void handleSdlEvent(const SDL_Event &event) override;

  private:
    struct Setting
    {
        std::string id, section, group, name, description, type, unit, depends;
        int minimum = 0, maximum = 100;
        std::vector<std::pair<std::string, std::string>> options;
    };
    struct Binding
    {
        KeyboardAction action;
        std::string id, name, group;
        // Where the key acts (catalog `context`, empty for play); keys of different contexts may be the same.
        std::string context;
    };
    struct Section
    {
        std::string id, name;
    };
    enum class Page
    {
        Home,
        Settings,
        Credits
    };
    void drawScreen(float deltaSeconds) override;
    void drawHome();
    void drawSettings(float deltaSeconds);
    // A slider's position (0-1) while the left button drags it: grabbed by a press inside its track and held until
    // release, so the pointer may leave the track and both ends are reachable.
    std::optional<float> sliderDragPosition(const std::string &id, const Rect &rect, bool enabled);
    void drawKeyboard(const std::string &prefix, const Rect &viewport);
    // The loot filter's window over Settings (MainMenuLootFilter.cpp, level_generation/ui/maw_loot_progress_20261025
    // view A): it edits the ruleset draft's filter, applied with the other settings.
    void drawLootFilter();
    void loadCatalog();
    void editSetting(const Setting &setting, const std::string &value);
    void chooseSetting(const Setting &setting);
    size_t dirtyCount() const;
    // A row's value in the draft or as applied; the Rules tab's rows read the game's ruleset options.
    std::string settingValue(const Setting &setting, bool applied = false) const;
    bool settingEnabled(const Setting &setting) const;
    void leaveSettings();
    void applySettings(bool leaveAfter = false);
    void restoreDefaults();
    void captureBinding(KeyboardAction action);
    void acceptBinding(InputBinding binding);
    void revertDisplay();
    // The main menu's update notice, question and progress (packaging/UPDATER_PLAN.md 10).
    void drawUpdates();
    void drawUpdateSettings(const std::string &prefix);
    void askAboutUpdates();
    void setUpdateCheck(const std::string &mode);
    void offerUpdate();
    void followUpdate();
    Actions m_actions;
    const GameDataRepository &m_gameData;
    GameSettings m_committed;
    GameSettings m_draft;
    std::optional<CurrentGame> m_currentGame;
    RulesetOptions m_rulesetDraft;
    std::vector<Setting> m_settings;
    std::vector<Binding> m_bindings;
    std::vector<Section> m_sections;
    std::optional<std::filesystem::path> m_latestSave;
    std::string m_latestSaveMap;
    std::string m_latestSaveLocation;
    std::optional<KeyboardAction> m_capture;
    // A modifier pressed while capturing: bound when released alone, passed over when a key follows (a mouse's side
    // button that sends a combination such as Ctrl+F9 binds F9).
    std::optional<SDL_Scancode> m_captureModifier;
    Page m_page = Page::Home;
    // Owned by the application so that reopening the menu returns to the last Settings section this session.
    std::string &m_section;
    std::string m_location, m_date, m_status, m_search;
    std::string m_bindingGroup = "All actions";
    bool m_paused = false;
    bool m_searchEditing = false;
    bool m_displayPreview = false;
    bool m_leaveAfterApply = false;
    bool m_suppressEscape = false;
    bool m_lootFilterOpen = false;
    float m_displaySeconds = 0;
    float m_scroll = 0;
    // The settings slider the left button grabbed; it follows the pointer until release (sliderDragPosition).
    std::string m_draggedSlider;
    GameUpdater *m_pUpdater = nullptr;
    bool m_updatesStarted = false;
    bool m_followingUpdate = false;
    std::string m_updateRelease;
};
} // namespace OpenYAMM::Game
