#include "game/ui/screens/MainMenuScreen.h"

#include "game/app/GameUpdater.h"
#include "game/data/GameDataRepository.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/ui/MenuSettingsModel.h"
#include "game/ui/screens/LoadGameScreen.h"

#include <yaml-cpp/yaml.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <set>
#include <stdexcept>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
std::string capitalized(const std::string &value)
{
    std::string result;
    bool upper = true;
    for (const unsigned char c : value)
    {
        if (c == '_' || c == '-')
        {
            upper = true;
            continue;
        }
        result += upper ? char(std::toupper(c)) : char(c);
        upper = false;
    }
    return result;
}
std::string lower(std::string value)
{
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return value;
}

// The catalog section whose rows are the ruleset options of the game in progress.
constexpr const char *GameSection = "game";

std::string rulesetSettingValue(const RulesetOptions &options, const std::string &id)
{
    const auto flag = [](bool value) { return std::string(value ? "true" : "false"); };
    if (id == "ruleset_difficulty")
    {
        return std::string(rulesetDifficultyId(options.difficulty));
    }
    if (id == "ruleset_progression")
    {
        return std::string(rulesetProgressionId(options.progression));
    }
    if (id == "ruleset_challenge")
    {
        return std::string(rulesetChallengeModeId(options.challengeMode));
    }
    if (id == "ruleset_randomizer")
    {
        return flag(options.randomizer);
    }
    if (id == "ruleset_homing")
    {
        return flag(options.preferences.homingProjectiles);
    }
    if (id == "ruleset_friendly_fire")
    {
        return flag(options.preferences.friendlyFire);
    }
    if (id == "ruleset_disintegrate")
    {
        return flag(options.preferences.disintegration);
    }
    if (id == "ruleset_trainer_hints")
    {
        return flag(options.preferences.trainerHints);
    }
    if (id == "ruleset_bow")
    {
        // On: the bow shoots (the preference is stored the other way round, as MAW's disableBow).
        return flag(!options.preferences.bowDisabled);
    }
    if (id == "ruleset_loot_filter")
    {
        // The whole filter, so a changed kind or "stay on the ground" counts as a change too.
        const RulesetLootFilter &filter = options.preferences.lootFilter;
        return std::string(rulesetLootFilterPresetId(filter.preset)) + ":" + std::to_string(filter.goldKinds) + ":"
            + (filter.leaveOnGround ? "ground" : "gold");
    }
    return {};
}

void setRulesetSettingValue(RulesetOptions &options, const std::string &id, const std::string &value)
{
    if (id == "ruleset_difficulty")
    {
        options.difficulty = parseRulesetDifficulty(value).value_or(options.difficulty);
    }
    else if (id == "ruleset_progression")
    {
        options.progression = parseRulesetProgression(value).value_or(options.progression);
    }
    else if (id == "ruleset_homing")
    {
        options.preferences.homingProjectiles = value == "true";
    }
    else if (id == "ruleset_friendly_fire")
    {
        options.preferences.friendlyFire = value == "true";
    }
    else if (id == "ruleset_disintegrate")
    {
        options.preferences.disintegration = value == "true";
    }
    else if (id == "ruleset_trainer_hints")
    {
        options.preferences.trainerHints = value == "true";
    }
    else if (id == "ruleset_bow")
    {
        options.preferences.bowDisabled = value != "true";
    }
    else if (id == "ruleset_loot_filter")
    {
        // A preset id, or the whole filter as rulesetSettingValue writes it.
        const size_t separator = value.find(':');
        const std::optional<RulesetLootFilterPreset> preset = parseRulesetLootFilterPreset(value.substr(0, separator));
        if (preset)
        {
            options.preferences.lootFilter =
                rulesetLootFilterWithPreset(*preset, options.preferences.lootFilter.leaveOnGround);
            const size_t second = separator == std::string::npos ? std::string::npos : value.find(':', separator + 1);
            if (second != std::string::npos)
            {
                options.preferences.lootFilter.goldKinds =
                    uint8_t(std::strtoul(value.substr(separator + 1, second - separator - 1).c_str(), nullptr, 10)
                            & ((1u << RulesetLootKindCount) - 1));
                options.preferences.lootFilter.leaveOnGround = value.substr(second + 1) == "ground";
            }
        }
    }
}
} // namespace

MainMenuScreen::MainMenuScreen(const Engine::AssetFileSystem &assets, const GameDataRepository &gameData,
                               GameAudioSystem *pAudio, const GameSettings &settings, Actions actions,
                               std::string &settingsSection, bool paused, std::string location, std::string date,
                               GameUpdater *pUpdater, std::optional<CurrentGame> currentGame)
    : MenuDesignScreen(assets, paused, pAudio), m_actions(std::move(actions)), m_gameData(gameData),
      m_committed(settings), m_draft(settings), m_currentGame(std::move(currentGame)), m_section(settingsSection),
      m_location(std::move(location)), m_date(std::move(date)), m_paused(paused),
      m_pUpdater(paused ? nullptr : pUpdater)
{
    if (m_currentGame)
    {
        m_rulesetDraft = m_currentGame->selection.options;
    }
    // A section left open in another game may not exist in this one.
    if (m_section == GameSection && !m_currentGame)
    {
        m_section = "gameplay";
    }
    if (!paused)
    {
        m_latestSave = LoadGameScreen::mostRecentSave(m_latestSaveMap);
    }
}

AppMode MainMenuScreen::mode() const
{
    return m_paused ? AppMode::PauseMenu : AppMode::MainMenu;
}

void MainMenuScreen::prepareForFirstFrame()
{
    loadDesign(m_paused ? "gameplay/menu" : "menu/main_menu");
}

void MainMenuScreen::onExit()
{
    if (m_displayPreview)
    {
        revertDisplay();
    }
}

void MainMenuScreen::loadCatalog()
{
    if (!m_settings.empty())
    {
        return;
    }
    const std::optional<std::string> text = assetFileSystem().readTextFile("ui/menu/settings_catalog.yml");
    if (!text)
    {
        throw std::runtime_error("Missing menu settings catalog");
    }
    const YAML::Node catalog = YAML::Load(*text);
    for (const YAML::Node &item : catalog["sections"])
    {
        if ((item["updater_only"].as<bool>(false) && m_pUpdater == nullptr)
            || (item["game_only"].as<bool>(false) && !m_currentGame))
        {
            continue;
        }
        m_sections.push_back({item["id"].as<std::string>(), item["name"].as<std::string>()});
    }
    for (const YAML::Node &item : catalog["settings"])
    {
        Setting setting;
        setting.id = item["id"].as<std::string>();
        setting.section = item["section"].as<std::string>();
        setting.group = item["group"].as<std::string>();
        setting.name = item["name"].as<std::string>();
        setting.description = item["desc"].as<std::string>();
        if (m_currentGame && item["ruleset_desc"])
        {
            setting.description = item["ruleset_desc"].as<std::string>();
        }
        setting.type = item["type"].as<std::string>();
        setting.unit = item["unit"].as<std::string>("");
        setting.depends = item["depends"].as<std::string>("");
        setting.minimum = item["min"].as<int>(0);
        setting.maximum = item["max"].as<int>(100);
        if (item["options"])
        {
            for (const YAML::Node &option : item["options"])
            {
                setting.options.emplace_back(option[0].as<std::string>(), option[1].as<std::string>());
            }
        }
        // An action row stores no setting; drawUpdateSettings draws the only one, update_now.
        if (setting.type == "action")
        {
            continue;
        }
        if (setting.section == GameSection)
        {
            if (!m_currentGame)
            {
                continue;
            }
            // The choices are the ruleset's own.
            const RulesetDefinition &definition = m_currentGame->definition;
            const auto offered = [&](const std::string &value)
            {
                if (setting.id == "ruleset_difficulty")
                {
                    const std::optional<RulesetDifficulty> difficulty = parseRulesetDifficulty(value);
                    return difficulty && std::find(definition.choices.difficulties.begin(),
                                                   definition.choices.difficulties.end(),
                                                   *difficulty) != definition.choices.difficulties.end();
                }
                if (setting.id == "ruleset_progression")
                {
                    const std::optional<RulesetProgression> progression = parseRulesetProgression(value);
                    return progression && std::find(definition.choices.progressions.begin(),
                                                    definition.choices.progressions.end(),
                                                    *progression) != definition.choices.progressions.end();
                }
                return true;
            };
            std::erase_if(setting.options, [&](const auto &option) { return !offered(option.first); });
            if (setting.id == "ruleset_name")
            {
                setting.options = {{m_currentGame->selection.id, definition.name}};
            }
            if ((setting.id == "ruleset_progression" && definition.choices.progressions.empty())
                || (setting.id == "ruleset_randomizer" && !definition.choices.randomizer)
                // Disintegration happens only in Road to Insanity and Beyond Madness.
                || (setting.id == "ruleset_disintegrate"
                    && m_currentGame->selection.options.challengeMode != RulesetChallengeMode::RoadToInsanity
                    && m_currentGame->selection.options.challengeMode != RulesetChallengeMode::BeyondMadness)
                || (setting.id.starts_with("ruleset_") && setting.group == "Preferences"
                    && !definition.choices.preferences))
            {
                continue;
            }
            m_settings.push_back(std::move(setting));
            continue;
        }
        menuSettingValue(m_draft, setting.id); // An unknown catalog field is an installation error.
        // Settings of the self-updater only exist where the game updates itself.
        if (item["updater_only"].as<bool>(false) && m_pUpdater == nullptr)
        {
            continue;
        }
        // A setting only one ruleset uses is left out of the pause menu of another ruleset's game; the main menu lists
        // it (audit STD4-2-5: the rarity glow does nothing in Standard).
        // A Standard game's pause menu has no m_currentGame.
        const std::string gameRuleset = item["game_ruleset"].as<std::string>("");
        if (!gameRuleset.empty() && m_paused
            && (m_currentGame ? m_currentGame->selection.id : std::string(StandardRulesetId)) != gameRuleset)
        {
            continue;
        }
#if defined(__ANDROID__)
        if (item["desktop_only"].as<bool>(false))
        {
            continue;
        }
#endif
        m_settings.push_back(std::move(setting));
    }
    for (const YAML::Node &item : catalog["bindings"])
    {
        const std::string id = item["id"].as<std::string>();
        // A ruleset's keys are listed only in the pause menu of a game with that ruleset.
        const std::string ruleset = item["ruleset"].as<std::string>("");
        const bool listed = ruleset.empty() || (m_currentGame && m_currentGame->selection.id == ruleset);
        bool found = false;
        for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
        {
            if (definition.implemented && definition.iniKey == id)
            {
                if (listed)
                {
                    m_bindings.push_back({definition.action, id, item["name"].as<std::string>(),
                                          item["group"].as<std::string>(), item["context"].as<std::string>("")});
                }
                found = true;
            }
        }
        if (!found)
        {
            throw std::runtime_error("Unknown menu binding: " + id);
        }
    }
}

void MainMenuScreen::drawScreen(float deltaSeconds)
{
    if (m_page == Page::Home)
    {
        drawHome();
    }
    else if (m_page == Page::Settings)
    {
        drawSettings(deltaSeconds);
    }
    else
    {
        loadDesign("menu/credits");
        beginDesign("Credits");
        drawDesign();
        if (button("github", designRect("CreditsProjectLink"), "OpenYAMM on GitHub", "button_quiet"))
        {
            SDL_OpenURL("https://github.com/pjasicek/OpenYAMM");
        }
        if (action("CreditsBackButton") || (!modalOpen() && keyPressed(SDL_SCANCODE_ESCAPE)))
        {
            m_page = Page::Home;
        }
    }
    drawConfirmation();
    m_suppressEscape = false;
}

void MainMenuScreen::drawHome()
{
    loadDesign(m_paused ? "gameplay/menu" : "menu/main_menu");
    beginDesign(m_paused ? "Menu" : "MainMenu");
    drawDesign();
    const auto settings = [this]()
    {
        loadCatalog();
        m_page = Page::Settings;
        m_scroll = 0;
    };
    const auto newGame = [this]()
    {
        if (m_paused)
        {
            confirm("Start a New Adventure?", "Unsaved progress in this adventure will be lost.",
                    {"Cancel", "New Game"},
                    [this](int choice)
                    {
                        if (choice == 1)
                        {
                            m_actions.newGame();
                        }
                    });
        }
        else
        {
            m_actions.newGame();
        }
    };
    const auto quit = [this]()
    {
        confirm("Leave OpenYAMM?",
                m_paused ? "Unsaved progress will be lost. Return to your desktop?" : "Return to your desktop?",
                {"Cancel", "Quit"},
                [this](int choice)
                {
                    if (choice == 1)
                    {
                        m_actions.quit();
                    }
                });
    };
    if (m_paused)
    {
        label("MenuTitle", m_location);
        label("MenuWorldAndDate", m_date);
        if (action("MenuButtonReturn") || (!modalOpen() && keyPressed(SDL_SCANCODE_ESCAPE)))
        {
            m_actions.resume();
            return;
        }
        if (action("MenuButtonSaveGame"))
        {
            m_actions.saveGame();
        }
        if (action("MenuButtonLoadGame"))
        {
            m_actions.loadGame();
        }
        if (action("MenuButtonSettings"))
        {
            settings();
        }
        if (action("MenuButtonNewGame"))
        {
            newGame();
        }
        if (action("MenuButtonMainMenu"))
        {
            confirm("Return to Main Menu?", "Unsaved progress in this adventure will be lost.", {"Cancel", "Main Menu"},
                    [this](int choice)
                    {
                        if (choice == 1)
                        {
                            m_actions.mainMenu();
                        }
                    });
        }
        if (action("MenuButtonQuit"))
        {
            quit();
        }
    }
    else
    {
        if (m_latestSave && m_latestSaveLocation.empty() && m_gameData.isBound())
        {
            m_latestSaveLocation = resolveSaveLocationName(m_gameData.mapEntries(), m_latestSaveMap);
        }
        label("MainMenuContinueInfo", m_latestSave ? m_latestSaveLocation : "Your adventure begins here");
        if (action("MainMenuContinueButton", m_latestSave.has_value()))
        {
            if (!m_actions.continueGame(*m_latestSave))
            {
                m_status = "The saved adventure could not be loaded.";
            }
        }
        if (action("MainMenuNewGameButton"))
        {
            newGame();
        }
        if (action("MainMenuLoadGameButton", m_latestSave.has_value()))
        {
            m_actions.loadGame();
        }
        if (action("MainMenuSettingsButton"))
        {
            settings();
        }
        if (action("MainMenuCreditsButton"))
        {
            m_page = Page::Credits;
        }
        if (action("MainMenuQuitButton"))
        {
            quit();
        }
        drawUpdates();
    }
    if (!m_status.empty())
    {
        const Rect status = m_paused ? canvasRect(310, 416, 420, 35) : canvasRect(563.2f, 438, 231.4667f, 28);
        textInRect(status, m_status, "menu_lucida", 11);
    }
}

void MainMenuScreen::drawUpdates()
{
    if (m_pUpdater == nullptr)
    {
        return;
    }

    textInRect(canvasRect(14, 456, 260, 16), "OpenYAMM " + m_pUpdater->installedVersion(), "menu_lucida", 9,
               0xff9fb6c4u);

    if (!m_updatesStarted)
    {
        m_updatesStarted = true;

        if (const std::optional<std::string> failed = m_pUpdater->takeRollbackNotice())
        {
            confirm("Update Undone", "OpenYAMM " + *failed + " did not start, so OpenYAMM "
                        + m_pUpdater->installedVersion() + " was restored. Your saves are unchanged.",
                    {"OK"}, [](int) {});
        }
        else if (m_committed.keepModifiedPacks)
        {
            // Updates are off and would replace the packs the player changed; Check Now says so (GameUpdater).
        }
        else if (m_committed.updateCheck == "ask")
        {
            askAboutUpdates();
        }
        else if (m_committed.updateCheck == "auto" && m_pUpdater->status().state == Engine::UpdateState::Idle)
        {
            m_pUpdater->check();
        }
    }

    const Engine::UpdateStatus status = m_pUpdater->status();

    if (m_followingUpdate)
    {
        followUpdate();
        return;
    }

    if (status.state == Engine::UpdateState::Available)
    {
        m_updateRelease = status.release;
    }

    std::string text;

    if (status.state == Engine::UpdateState::Ready)
    {
        text = "Restart to play OpenYAMM " + status.release;
    }
    else if (status.state == Engine::UpdateState::Available
             || (status.state == Engine::UpdateState::Failed && !m_updateRelease.empty()))
    {
        text = "Update to OpenYAMM " + m_updateRelease + " ("
            + std::to_string((status.totalBytes + 999999) / 1000000) + " MB)";
    }

    if (!text.empty() && button("update", canvasRect(14, 430, 250, 22), text, "button_quiet") && !modalOpen())
    {
        offerUpdate();
    }
}

void MainMenuScreen::drawUpdateSettings(const std::string &prefix)
{
    // The Updates tab's version row: the installed version, the update status and one button that checks again or,
    // in the main menu, installs what a check found. From the pause menu it only checks: on Android an update closes
    // the game, and the unsaved game with it.
    if (m_followingUpdate)
    {
        followUpdate();
    }

    const Engine::UpdateStatus status = m_pUpdater->status();
    const std::string size = std::to_string((status.totalBytes + 999999) / 1000000) + " MB";
    std::string text = "Check Now looks for a new version on jasicek.net. Nothing downloads without asking.";
    std::string buttonText = "Check Now";
    bool enabled = true;
    bool install = false;

    if (status.state == Engine::UpdateState::Checking)
    {
        text = "Looking for a new version on jasicek.net...";
        buttonText = "Checking...";
        enabled = false;
    }
    else if (status.state == Engine::UpdateState::UpToDate)
    {
        text = "This is the newest version.";
    }
    else if (status.state == Engine::UpdateState::Failed)
    {
        text = "The last check failed: " + status.message;
    }
    else if (status.state == Engine::UpdateState::Available)
    {
        m_updateRelease = status.release;
        text = "OpenYAMM " + status.release + " is available (" + size + ")."
            + (m_paused ? " Update it from the main menu." : "");
        buttonText = m_paused ? "Check Now" : "Update";
        install = !m_paused;
    }
    else if (status.state == Engine::UpdateState::Downloading)
    {
        text = "Downloading OpenYAMM " + m_updateRelease + ": " + std::to_string(status.doneBytes / 1000000) + " of "
            + size + ".";
        buttonText = "Downloading...";
        enabled = false;
    }
    else if (status.state == Engine::UpdateState::Ready)
    {
        text = "OpenYAMM " + status.release + " is downloaded. Restart"
            + (m_paused ? " from the main menu" : "") + " to play it.";
        buttonText = "Restart";
        enabled = !m_paused;
        install = !m_paused;
    }

    const std::string id = prefix + "UpdateNow";
    label(id + "Label", "Installed: OpenYAMM " + m_pUpdater->installedVersion(), 0, -m_scroll);
    label(id + "Description", text, 0, -m_scroll);
    Rect rect = designRect(id + "Control");
    rect.y -= m_scroll * designScale();

    if (button("update-now", rect, buttonText, "button_small", enabled) && !modalOpen())
    {
        if (install)
        {
            offerUpdate();
        }
        else
        {
            m_pUpdater->check();
        }
    }
}

void MainMenuScreen::askAboutUpdates()
{
    confirm("Check for Updates?",
            "OpenYAMM can look for a new version on jasicek.net when it starts. Nothing is downloaded without asking.",
            {"Never", "At start"},
            [this](int choice)
            {
                if (choice < 0)
                {
                    return;
                }
                setUpdateCheck(choice == 1 ? "auto" : "off");
                if (choice == 1)
                {
                    m_pUpdater->check();
                }
            });
}

void MainMenuScreen::setUpdateCheck(const std::string &mode)
{
    GameSettings settings = m_committed;
    settings.updateCheck = mode;
    std::string error;
    if (m_actions.applySettings(settings, true, error))
    {
        m_committed.updateCheck = mode;
        m_draft.updateCheck = mode;
    }
}

void MainMenuScreen::offerUpdate()
{
    const Engine::UpdateStatus status = m_pUpdater->status();

    if (status.state == Engine::UpdateState::Ready)
    {
        followUpdate();
        return;
    }

    const std::string size = std::to_string((status.totalBytes + 999999) / 1000000) + " MB";
    const std::string body = m_pUpdater->updatesInGame()
        ? "Downloads " + size + ". Your saves and settings stay as they are."
        : "Downloads " + size + " in the update screen. Your saves and settings stay as they are.";
    const bool hasNotesPage = !status.notesUrl.empty();
    std::vector<std::string> choices = {"Later", "Update"};

    if (hasNotesPage)
    {
        choices.insert(choices.begin() + 1, "Release Notes");
    }

    confirm("Update to OpenYAMM " + m_updateRelease + "?", body, choices,
            [this, hasNotesPage, url = status.notesUrl](int choice)
            {
                if (hasNotesPage && choice == 1)
                {
                    SDL_OpenURL(url.c_str());
                    return;
                }
                if (choice != (hasNotesPage ? 2 : 1))
                {
                    return;
                }
                m_pUpdater->startUpdate();
                if (!m_pUpdater->updatesInGame())
                {
                    // The Android update screen takes over; the game starts again from it.
                    m_actions.quit();
                    return;
                }
                m_followingUpdate = true;
                confirm("Updating OpenYAMM", "Starting the download...", {"Cancel"},
                        [this](int)
                        {
                            m_pUpdater->cancel();
                            m_followingUpdate = false;
                        });
            });
    // The signed manifest's notes (the release tag's message), whole: the box scrolls when they are long.
    setModalNotes(status.notes);
}

void MainMenuScreen::followUpdate()
{
    const Engine::UpdateStatus status = m_pUpdater->status();

    // Until the worker reports its first progress, the update is still Available.
    if (status.state == Engine::UpdateState::Downloading || status.state == Engine::UpdateState::Available)
    {
        setModalBody(status.state == Engine::UpdateState::Available
                         ? "Starting the download..."
                         : status.message + "\n" + std::to_string(status.doneBytes / 1000000) + " of "
                             + std::to_string((status.totalBytes + 999999) / 1000000) + " MB");
        return;
    }

    if (m_followingUpdate)
    {
        closeConfirmation();
        m_followingUpdate = false;
    }

    if (status.state == Engine::UpdateState::Failed)
    {
        confirm("Update Failed", status.message, {"OK"}, [](int) {});
        return;
    }

    if (status.state == Engine::UpdateState::Ready)
    {
        confirm("OpenYAMM " + status.release + " Is Ready", "Restart now to play the new version.",
                {"Later", "Restart Now"},
                [this](int choice)
                {
                    if (choice != 1)
                    {
                        return;
                    }
                    std::string error;
                    if (m_pUpdater->restartIntoUpdate(error))
                    {
                        m_actions.quit();
                    }
                    else
                    {
                        confirm("Update Failed", error, {"OK"}, [](int) {});
                    }
                });
    }
}

size_t MainMenuScreen::dirtyCount() const
{
    size_t count = 0;
    for (const Setting &setting : m_settings)
    {
        if (settingValue(setting) != settingValue(setting, true))
        {
            ++count;
        }
    }
    for (const Binding &binding : m_bindings)
    {
        if (!sameMenuBinding(m_draft.keyboard.binding(binding.action), m_committed.keyboard.binding(binding.action)))
        {
            ++count;
        }
    }
    // Restoring values that already equal their defaults still releases them from the player's file.
    if (count == 0 && m_draft.fileState.storedKeys != m_committed.fileState.storedKeys)
    {
        ++count;
    }
    return count;
}

std::string MainMenuScreen::settingValue(const Setting &setting, bool applied) const
{
    if (setting.section != GameSection)
    {
        return menuSettingValue(applied ? m_committed : m_draft, setting.id);
    }
    if (setting.id == "ruleset_name")
    {
        return m_currentGame->selection.id;
    }
    return rulesetSettingValue(applied ? m_currentGame->selection.options : m_rulesetDraft, setting.id);
}

bool MainMenuScreen::settingEnabled(const Setting &setting) const
{
    if (setting.section != GameSection)
    {
        return (setting.depends.empty() || menuSettingValue(m_draft, setting.depends) == "true")
            && !(setting.id == "resolution" && m_draft.windowMode == WindowMode::WindowedFullscreen);
    }
    const RulesetOptions &applied = m_currentGame->selection.options;
    if (setting.id == "ruleset_difficulty")
    {
        // Nightmare and the challenge modes keep their difficulty.
        return !applied.difficultyLocked() && setting.options.size() > 1;
    }
    if (setting.id == "ruleset_progression")
    {
        return !rulesetChallengeModeProgression(applied.challengeMode) && setting.options.size() > 1;
    }
    return setting.group == "Preferences";
}

void MainMenuScreen::leaveSettings()
{
    if (dirtyCount() == 0)
    {
        m_page = Page::Home;
        setTextEditing(false);
        return;
    }
    confirm("Unapplied Changes", "Apply your changes before leaving Settings?", {"Stay", "Discard", "Apply"},
            [this](int choice)
            {
                if (choice == 1)
                {
                    m_draft = m_committed;
                    if (m_currentGame)
                    {
                        m_rulesetDraft = m_currentGame->selection.options;
                    }
                    m_page = Page::Home;
                    setTextEditing(false);
                }
                if (choice == 2)
                {
                    applySettings(true);
                }
            }, true);
}

void MainMenuScreen::revertDisplay()
{
    std::string error;
    m_actions.applySettings(m_committed, false, error);
    m_displayPreview = false;
    m_draft.windowMode = m_committed.windowMode;
    m_draft.resolutionWidth = m_committed.resolutionWidth;
    m_draft.resolutionHeight = m_committed.resolutionHeight;
    m_draft.verticalSync = m_committed.verticalSync;
    m_status = error.empty() ? "Previous display settings restored." : error;
}

void MainMenuScreen::applySettings(bool leaveAfter)
{
    if (m_currentGame && m_rulesetDraft != m_currentGame->selection.options)
    {
        std::string rulesetError;
        if (!m_actions.applyRuleset || !m_actions.applyRuleset(m_rulesetDraft, rulesetError))
        {
            m_status = rulesetError;
            return;
        }
        m_currentGame->selection.options = m_rulesetDraft;
    }
    const bool displayChanged =
        m_draft.windowMode != m_committed.windowMode || m_draft.resolutionWidth != m_committed.resolutionWidth ||
        m_draft.resolutionHeight != m_committed.resolutionHeight || m_draft.verticalSync != m_committed.verticalSync;
    std::string error;
    if (!m_actions.applySettings(m_draft, !displayChanged, error))
    {
        m_status = error;
        return;
    }
    if (displayChanged)
    {
        m_displayPreview = true;
        m_displaySeconds = 15;
        m_leaveAfterApply = leaveAfter;
        confirm("Keep Display Settings?", "Reverting in 15 seconds.", {"Revert", "Keep"},
                [this](int choice)
                {
                    if (choice != 1)
                    {
                        revertDisplay();
                        return;
                    }
                    std::string message;
                    if (m_actions.applySettings(m_draft, true, message))
                    {
                        m_displayPreview = false;
                        m_committed = m_draft;
                        m_status = "Settings saved.";
                        if (m_leaveAfterApply)
                        {
                            m_page = Page::Home;
                        }
                    }
                    else
                    {
                        revertDisplay();
                        m_status = message;
                    }
                }, true);
    }
    else
    {
        m_committed = m_draft;
        m_status = "Settings saved.";
        if (leaveAfter)
        {
            m_page = Page::Home;
        }
    }
}

void MainMenuScreen::restoreDefaults()
{
    confirm("Restore Defaults?",
            m_section == "controls" ? "Restore mouse controls, the control preset and its keyboard bindings?"
                                    : "Restore the current Settings section to its defaults?",
            {"Cancel", "Restore"},
            [this](int choice)
            {
                if (choice != 1)
                {
                    return;
                }
                const GameSettings defaults = GameSettings::createDefault();
                // Menu setting ids are the INI key names; released keys follow later default changes again.
                std::vector<std::string> restoredKeys;
                if (m_section == GameSection)
                {
                    // What the ruleset lets the player change: its default preferences, difficulty and progression.
                    const RulesetOptions defaults = m_currentGame->definition.defaultOptions();
                    const RulesetOptions &applied = m_currentGame->selection.options;
                    m_rulesetDraft.preferences = defaults.preferences;
                    if (!applied.difficultyLocked())
                    {
                        m_rulesetDraft.difficulty = defaults.difficulty;
                    }
                    if (!rulesetChallengeModeProgression(applied.challengeMode))
                    {
                        m_rulesetDraft.progression = defaults.progression;
                    }
                    return;
                }
                if (m_section == "keyboard")
                {
                    m_draft.keyboard.restoreDefaults(m_draft.controlScheme);
                    restoredKeys.push_back("input.");
                }
                else
                {
                    for (const Setting &setting : m_settings)
                    {
                        if (setting.section == m_section)
                        {
                            setMenuSettingValue(m_draft, setting.id, menuSettingValue(defaults, setting.id));
                            restoredKeys.push_back(setting.id);
                        }
                    }
                    if (m_section == "controls")
                    {
                        m_draft.keyboard.restoreDefaults(m_draft.controlScheme);
                        restoredKeys.push_back("input.");
                    }
                    if (m_section == "video")
                    {
                        // Graphics quality presets also set these INI-only fields.
                        m_draft.terrainSubdivision = defaults.terrainSubdivision;
                        m_draft.terrainAntiTiling = defaults.terrainAntiTiling;
                        m_draft.skyResolutionScale = defaults.skyResolutionScale;
                        restoredKeys.insert(
                            restoredKeys.end(), {"terrain_subdivision", "terrain_antitiling", "sky_resolution_scale"});
                    }
                }
                releaseStoredSettings(m_draft, restoredKeys);
            });
}

void MainMenuScreen::editSetting(const Setting &setting, const std::string &value)
{
    if (setting.section == GameSection)
    {
        if (setting.id == "ruleset_difficulty" && value == rulesetDifficultyId(RulesetDifficulty::Nightmare)
            && m_rulesetDraft.difficulty != RulesetDifficulty::Nightmare)
        {
            confirm("Choose Nightmare?", "Nightmare can never be lowered again in this adventure.",
                    {"Cancel", "Nightmare"},
                    [this, setting, value](int choice)
                    {
                        if (choice == 1)
                        {
                            setRulesetSettingValue(m_rulesetDraft, setting.id, value);
                        }
                    });
        }
        else
        {
            setRulesetSettingValue(m_rulesetDraft, setting.id, value);
        }
        m_status.clear();
        return;
    }
    if (setting.id == "control_scheme" && menuSettingValue(m_draft, setting.id) != value)
    {
        confirm("Change Control Preset?", "This also resets the keyboard bindings for the selected preset.",
                {"Cancel", "Change"},
                [this, value](int choice)
                {
                    if (choice == 1)
                    {
                        setMenuSettingValue(m_draft, "control_scheme", value);
                        m_draft.keyboard.restoreDefaults(m_draft.controlScheme);
                    }
                });
    }
    else
    {
        setMenuSettingValue(m_draft, setting.id, value);
    }
    m_status.clear();
}

void MainMenuScreen::chooseSetting(const Setting &setting)
{
    std::vector<std::pair<std::string, std::string>> choices = setting.options;
    if (setting.id == "resolution")
    {
        std::set<std::pair<int, int>> sizes;
        SDL_Window *pWindow = SDL_GetKeyboardFocus();
        const SDL_DisplayID display = pWindow ? SDL_GetDisplayForWindow(pWindow) : SDL_GetPrimaryDisplay();
        int count = 0;
        SDL_DisplayMode **pModes = SDL_GetFullscreenDisplayModes(display, &count);
        for (int i = 0; pModes != nullptr && i < count; ++i)
        {
            if (pModes[i]->w >= 640 && pModes[i]->h >= 480)
            {
                sizes.emplace(pModes[i]->w, pModes[i]->h);
            }
        }
        SDL_free(pModes);
        if (m_draft.windowMode == WindowMode::Windowed)
        {
            SDL_Rect bounds{};
            if (SDL_GetDisplayUsableBounds(display, &bounds))
            {
                for (const std::pair<int, int> size :
                     {std::pair{800, 600}, {1024, 768}, {1280, 720}, {1280, 800}, {1600, 900}, {1920, 1080}})
                {
                    if (size.first <= bounds.w && size.second <= bounds.h)
                    {
                        sizes.insert(size);
                    }
                }
            }
        }
        sizes.emplace(m_draft.resolutionWidth, m_draft.resolutionHeight);
        for (const auto &[width, height] : sizes)
        {
            const std::string value = std::to_string(width) + "x" + std::to_string(height);
            choices.emplace_back(value, std::to_string(width) + " x " + std::to_string(height));
        }
    }
    std::vector<std::string> labels;
    for (const auto &[value, label] : choices)
    {
        labels.push_back(label);
    }
    confirm(setting.name, "Choose a value", labels,
            [this, setting, choices](int index)
            {
                if (index >= 0)
                {
                    editSetting(setting, choices[size_t(index)].first);
                }
            }, true);
}

void MainMenuScreen::drawSettings(float deltaSeconds)
{
    loadCatalog();
    const std::string prefix = "Settings" + capitalized(m_section);
    loadDesign("gameplay/settings_" + m_section);
    beginDesign(prefix);
    drawDesign();
    if (m_lootFilterOpen)
    {
        drawLootFilter();
        return;
    }
    if (m_displayPreview)
    {
        m_displaySeconds -= deltaSeconds;
        setModalBody("Reverting in " + std::to_string(std::max(0, int(std::ceil(m_displaySeconds)))) + " seconds.");
        if (m_displaySeconds <= 0)
        {
            closeConfirmation();
            revertDisplay();
        }
    }
    if (!modalOpen() && !m_suppressEscape && keyPressed(SDL_SCANCODE_ESCAPE))
    {
        leaveSettings();
        return;
    }
    for (const Section &section : m_sections)
    {
        const std::string id = prefix + "Tab" + capitalized(section.id);
        if (button(id, designRect(id), section.name, "tab", true, section.id == m_section))
        {
            m_section = section.id;
            m_scroll = 0;
            m_searchEditing = false;
            setTextEditing(false);
            return;
        }
    }
    if (action(prefix + "DefaultsButton"))
    {
        restoreDefaults();
    }
    if (action(prefix + "BackButton"))
    {
        leaveSettings();
        return;
    }
    if (action(prefix + "RevertButton", dirtyCount() > 0))
    {
        m_draft = m_committed;
        if (m_currentGame)
        {
            m_rulesetDraft = m_currentGame->selection.options;
        }
        m_status.clear();
    }
    if (action(prefix + "ApplyButton", dirtyCount() > 0))
    {
        applySettings();
    }
    label(prefix + "DirtyStatus", !m_status.empty()   ? m_status
                                  : dirtyCount() == 0 ? "Your settings are up to date."
                                                      : std::to_string(dirtyCount()) + " unapplied changes");
    const Rect viewport = designRect(prefix + "ScrollViewport");
    if (m_section == "keyboard")
    {
        drawKeyboard(prefix, viewport);
        return;
    }
    // A row left out of this menu (game_ruleset) leaves no scroll room or group heading behind; such rows close their
    // section.
    std::unordered_set<std::string> listedDescriptions;
    std::unordered_set<std::string> listedGroups;
    for (const Setting &setting : m_settings)
    {
        if (setting.section == m_section)
        {
            listedDescriptions.insert(prefix + capitalized(setting.id) + "Description");
            listedGroups.insert(setting.group);
        }
    }
    float contentHeight = 0;
    for (const std::string &id : m_designLayouts.sortedLayoutIdsForScreenCached(prefix))
    {
        if (id.find("Description") == std::string::npos || id == prefix + "Description"
            || (id.ends_with("Description") && !listedDescriptions.contains(id)))
        {
            continue;
        }
        const Rect rect = designRect(id);
        contentHeight = std::max(contentHeight, (rect.y + rect.height - viewport.y) / designScale() + 14);
    }
    if (m_section == "controls")
    {
        contentHeight += 55;
    }
    scrollViewport(viewport, contentHeight, m_scroll);
    setDesignClip(viewport);
    for (int group = 0;; ++group)
    {
        const std::string id = prefix + "Group" + std::to_string(group);
        const auto *pItem = m_designLayouts.findElement(id);
        if (!pItem)
        {
            break;
        }
        if (listedGroups.contains(pItem->labelText))
        {
            label(id, pItem->labelText, 0, -m_scroll);
        }
    }
    for (const Setting &setting : m_settings)
    {
        if (setting.section != m_section)
        {
            continue;
        }
        const std::string id = prefix + capitalized(setting.id);
        label(id + "Label", setting.name, 0, -m_scroll);
        label(id + "Description", setting.description, 0, -m_scroll);
        Rect rect = designRect(id + "Control");
        rect.y -= m_scroll * designScale();
        const bool enabled = settingEnabled(setting);
        const std::string value = settingValue(setting);
        if (setting.type == "toggle")
        {
            if (button(id, rect, "", value == "true" ? "toggle_on" : "toggle_off", enabled))
            {
                editSetting(setting, value == "true" ? "false" : "true");
            }
            textInRect({rect.x + 35 * designScale(), rect.y, rect.width - 40 * designScale(), rect.height},
                       value == "true" ? "On" : "Off", "menu_lucida", 13.3333f, enabled ? 0xffc6dfeau : 0xff6b777au,
                       true);
        }
        else if (setting.type == "select")
        {
            std::string display = value;
            for (const auto &[option, name] : setting.options)
            {
                if (option == value)
                {
                    display = name;
                }
            }
            if (selectBox(id, rect, display, enabled))
            {
                chooseSetting(setting);
            }
        }
        else if (setting.type == "window")
        {
            // The loot filter: its preset, and a window with the rest.
            std::string display = value.substr(0, value.find(':'));
            for (const auto &[option, name] : setting.options)
            {
                if (option == display)
                {
                    display = name;
                }
            }
            if (selectBox(id, rect, display, enabled))
            {
                m_lootFilterOpen = true;
            }
        }
        else if (setting.type == "steps")
        {
            // A slider snapping to its options; a value that is none of them (Custom) shows no thumb.
            button(id, rect, "", "text_field", enabled);
            const int count = int(setting.options.size());
            int current = -1;
            std::string display = capitalized(value);
            for (int index = 0; index < count; ++index)
            {
                if (setting.options[size_t(index)].first == value)
                {
                    current = index;
                    display = setting.options[size_t(index)].second;
                }
            }
            const auto stepX = [&](int index)
            { return rect.x + rect.width * float(index) / float(std::max(1, count - 1)); };
            const float y = rect.y + rect.height / 2;
            drawSolidRect({rect.x, y - 2, rect.width, 4}, 0xff273629u);
            if (current >= 0)
            {
                drawSolidRect({rect.x, y - 2, stepX(current) - rect.x, 4}, 0xff6a93acu);
            }
            for (int index = 0; index < count; ++index)
            {
                drawSolidRect({stepX(index) - 1, y - 5, 2, 10}, index <= current ? 0xff6a93acu : 0xff3d5163u);
            }
            if (current >= 0)
            {
                drawSolidRect({stepX(current) - 4, y - 7, 8, 14}, 0xff7bbad8u);
            }
            int chosen = -1;
            if (const std::optional<float> position = sliderDragPosition(id, rect, enabled))
            {
                chosen = int(std::round(*position * float(count - 1)));
            }
            if (enabled && focused(id))
            {
                const int delta = int(keyPressed(SDL_SCANCODE_RIGHT)) - int(keyPressed(SDL_SCANCODE_LEFT));
                if (delta != 0)
                {
                    chosen = current < 0 ? count / 2 : std::clamp(current + delta, 0, count - 1);
                }
            }
            if (chosen >= 0 && chosen != current)
            {
                editSetting(setting, setting.options[size_t(chosen)].first);
            }
            label(id + "Value", display, 0, -m_scroll);
        }
        else
        {
            button(id, rect, "", "text_field", enabled);
            const int amount = std::stoi(value);
            const float fraction = float(amount - setting.minimum) / std::max(1, setting.maximum - setting.minimum);
            const float y = rect.y + rect.height / 2;
            drawSolidRect({rect.x, y - 2, rect.width, 4}, 0xff273629u);
            drawSolidRect({rect.x, y - 2, rect.width * fraction, 4}, 0xff6a93acu);
            drawSolidRect({rect.x + rect.width * fraction - 4, y - 7, 8, 14}, 0xff7bbad8u);
            if (const std::optional<float> position = sliderDragPosition(id, rect, enabled))
            {
                editSetting(setting, std::to_string(int(std::round(setting.minimum +
                                                                   *position * (setting.maximum - setting.minimum)))));
            }
            if (enabled && focused(id))
            {
                const int delta = int(keyPressed(SDL_SCANCODE_RIGHT)) - int(keyPressed(SDL_SCANCODE_LEFT));
                if (delta != 0)
                {
                    editSetting(setting, std::to_string(std::clamp(amount + delta, setting.minimum, setting.maximum)));
                }
            }
            label(id + "Value", value + setting.unit, 0, -m_scroll);
        }
    }
    if (m_section == "updates" && m_pUpdater != nullptr)
    {
        drawUpdateSettings(prefix);
    }
    if (m_section == "controls")
    {
        Rect rect = designRect(prefix + "KeyboardButton");
        rect.y -= m_scroll * designScale();
        if (button("configure-keyboard", rect, "Configure Keyboard", "button_small"))
        {
            m_section = "keyboard";
            m_scroll = 0;
        }
    }
    setDesignClip(std::nullopt);
}

std::optional<float> MainMenuScreen::sliderDragPosition(const std::string &id, const Rect &rect, bool enabled)
{
    if (!leftMouseDown())
    {
        if (m_draggedSlider == id)
        {
            m_draggedSlider.clear();
        }

        return std::nullopt;
    }

    if (leftMouseJustPressed())
    {
        if (enabled && !modalOpen() && pointerInside(rect))
        {
            m_draggedSlider = id;
            cancelContentDrag();
        }
        else if (m_draggedSlider == id)
        {
            m_draggedSlider.clear();
        }
    }

    if (m_draggedSlider != id || !enabled || modalOpen())
    {
        return std::nullopt;
    }

    // The ends saturate half a thumb inside the track, and the pointer may leave the track while dragging.
    const float inset = std::min(4.0f, rect.width / 4);
    return std::clamp((mouseX() - rect.x - inset) / std::max(1.0f, rect.width - 2 * inset), 0.0f, 1.0f);
}

void MainMenuScreen::drawKeyboard(const std::string &prefix, const Rect &viewport)
{
    if (m_searchEditing &&
        (keyPressed(SDL_SCANCODE_TAB) || (leftMouseJustPressed() && !pointerInside(designRect(prefix + "Search")))))
    {
        m_searchEditing = false;
        setTextEditing(false);
    }
    if (button("binding-search", designRect(prefix + "Search"), "", "text_field"))
    {
        m_searchEditing = true;
        setTextEditing(true);
    }
    label(prefix + "Search", m_search.empty() ? "Search actions or keys..." : m_search + (m_searchEditing ? "_" : ""));
    if (selectBox("binding-filter", designRect(prefix + "GroupFilter"), m_bindingGroup, true, 12.16f))
    {
        std::vector<std::string> groups = {"All actions"};
        for (const Binding &binding : m_bindings)
        {
            if (std::find(groups.begin(), groups.end(), binding.group) == groups.end())
            {
                groups.push_back(binding.group);
            }
        }
        confirm("Action Group", "", groups,
                [this, groups](int index)
                {
                    if (index >= 0)
                    {
                        m_bindingGroup = groups[index];
                        m_scroll = 0;
                    }
                }, true);
    }
    std::vector<const Binding *> filtered;
    for (const Binding &binding : m_bindings)
    {
        const std::string key = inputBindingDisplayName(m_draft.keyboard.binding(binding.action));
        if ((m_bindingGroup == "All actions" || m_bindingGroup == binding.group) &&
            lower(binding.name + " " + binding.group + " " + key).find(lower(m_search)) != std::string::npos)
        {
            filtered.push_back(&binding);
        }
    }
    const bool fixed = (m_bindingGroup == "All actions" || m_bindingGroup == "System") && m_search.empty();
    const float contentHeight = std::ceil(filtered.size() / 2.0f) * 30 + (fixed ? 85 : 0);
    scrollViewport(viewport, contentHeight, m_scroll);
    if (m_capture && mouseWheelDelta() != 0.0f)
    {
        acceptBinding(mouseWheelInputBinding(mouseWheelDelta()));
    }
    setDesignClip(viewport);
    const float scale = designScale();
    for (size_t i = 0; i < filtered.size(); ++i)
    {
        const Binding &binding = *filtered[i];
        const float width = (viewport.width - 12 * scale) / 2;
        const Rect rect{viewport.x + float(i % 2) * (width + 10 * scale),
                        viewport.y + (float(i / 2) * 30 - m_scroll) * scale, width, 29 * scale};
        textInRect({rect.x + 5 * scale, rect.y, width - 76 * scale, 18 * scale}, binding.name, "menu_arrus", 12.8f);
        textInRect({rect.x + 5 * scale, rect.y + 17 * scale, width - 76 * scale, 10 * scale}, binding.group,
                   "menu_lucida", 7.68f, 0xff99aaa0u);
        const Rect keyRect{rect.x + width - 66 * scale, rect.y + 3 * scale, 64 * scale, 23 * scale};
        if (button("binding-" + binding.id, keyRect, "", "keycap"))
        {
            captureBinding(binding.action);
        }
        textInRect(keyRect, inputBindingDisplayName(m_draft.keyboard.binding(binding.action)), "menu_lucida", 10.88f,
                   0xffc6dfeau, true);
    }
    if (fixed)
    {
        const float y = viewport.y + (std::ceil(filtered.size() / 2.0f) * 30 + 8 - m_scroll) * scale;
        textInRect({viewport.x + 5 * scale, y, viewport.width, 24 * scale}, "Fixed shortcuts", "fondamento", 14);
        textInRect({viewport.x + 5 * scale, y + 25 * scale, viewport.width, 50 * scale},
                   "F9  Quicksave       F10  Quickload\n1-5  Select party member       Escape  Open / close menu",
                   "menu_lucida", 11);
    }
    if (filtered.empty() && !fixed)
    {
        textInRect(viewport, "No matching actions", "menu_arrus", 15, 0xffc6dfeau, true);
    }
    setDesignClip(std::nullopt);
}

void MainMenuScreen::captureBinding(KeyboardAction action)
{
    m_searchEditing = false;
    setTextEditing(false);
    m_capture = action;
    m_captureModifier.reset();
    confirm("Assign Key", std::string(keyboardBindingDefinition(action).label) +
            "\nPress a key, mouse button, or scroll the wheel.",
            {"Cancel", "Clear", "Left Mouse"},
            [this, action](int choice)
            {
                if (choice == 2)
                {
                    acceptBinding(mouseButtonInputBinding(SDL_BUTTON_LEFT));
                    return;
                }
                if (choice == 1)
                {
                    m_draft.keyboard.setBinding(action, InputBinding{});
                }
                m_capture.reset();
            });
}

void MainMenuScreen::acceptBinding(InputBinding binding)
{
    if (!m_capture)
    {
        return;
    }
    const KeyboardAction target = *m_capture;
    if (reservedMenuBinding(binding, target))
    {
        setModalBody("That key is reserved. Choose another key.");
        return;
    }
    const auto targetBinding = std::find_if(m_bindings.begin(), m_bindings.end(),
                                            [target](const Binding &candidate) { return candidate.action == target; });
    const std::string context = targetBinding != m_bindings.end() ? targetBinding->context : "";
    std::optional<KeyboardAction> conflict;
    for (const Binding &candidate : m_bindings)
    {
        if (candidate.action != target && candidate.context == context
            && sameMenuBinding(m_draft.keyboard.binding(candidate.action), binding))
        {
            conflict = candidate.action;
        }
    }
    m_capture.reset();
    closeConfirmation();
    if (conflict)
    {
        confirm("Key Already Assigned",
                inputBindingDisplayName(binding) + " is assigned to " +
                    std::string(keyboardBindingDefinition(*conflict).label) + ". Swap the two actions?",
                {"Cancel", "Swap"},
                [this, target, binding, conflict](int choice)
                {
                    if (choice == 1)
                    {
                        m_draft.keyboard.setBinding(*conflict, m_draft.keyboard.binding(target));
                        m_draft.keyboard.setBinding(target, binding);
                    }
                });
    }
    else
    {
        m_draft.keyboard.setBinding(target, binding);
    }
}

void MainMenuScreen::handleSdlEvent(const SDL_Event &event)
{
    if (m_capture)
    {
        if (event.type == SDL_EVENT_KEY_DOWN && !event.key.repeat)
        {
            if (event.key.scancode == SDL_SCANCODE_ESCAPE)
            {
                m_capture.reset();
                closeConfirmation();
                m_suppressEscape = true;
                return;
            }
            const bool modifierKey =
                event.key.scancode >= SDL_SCANCODE_LCTRL && event.key.scancode <= SDL_SCANCODE_RGUI;
            if (modifierKey)
            {
                if (!m_captureModifier)
                {
                    m_captureModifier = event.key.scancode;
                }
                return;
            }
            // Bindings are single keys: a combination binds its key.
            m_captureModifier.reset();
            acceptBinding(keyboardInputBinding(event.key.scancode));
        }
        if (event.type == SDL_EVENT_KEY_UP && m_captureModifier && event.key.scancode == *m_captureModifier)
        {
            const SDL_Scancode modifier = *m_captureModifier;
            m_captureModifier.reset();
            acceptBinding(keyboardInputBinding(modifier));
        }
        if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && event.button.button != SDL_BUTTON_LEFT)
        {
            acceptBinding(mouseButtonInputBinding(event.button.button));
        }
        return;
    }
    if (m_searchEditing && !modalOpen())
    {
        if (event.type == SDL_EVENT_KEY_DOWN &&
            (event.key.scancode == SDL_SCANCODE_ESCAPE || event.key.scancode == SDL_SCANCODE_RETURN))
        {
            m_searchEditing = false;
            setTextEditing(false);
            m_suppressEscape = true;
            return;
        }
        if (event.type == SDL_EVENT_TEXT_INPUT)
        {
            m_search += event.text.text;
            m_scroll = 0;
        }
        if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_BACKSPACE && !m_search.empty())
        {
            m_search.pop_back();
            m_scroll = 0;
        }
    }
}
} // namespace OpenYAMM::Game
