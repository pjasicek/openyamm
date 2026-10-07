#include "game/ui/screens/MainMenuScreen.h"

#include "game/data/GameDataRepository.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/ui/MenuSettingsModel.h"
#include "game/ui/screens/LoadGameScreen.h"

#include <yaml-cpp/yaml.h>
#include <algorithm>
#include <cmath>
#include <set>
#include <stdexcept>

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
} // namespace

MainMenuScreen::MainMenuScreen(const Engine::AssetFileSystem &assets, const GameDataRepository &gameData,
                               GameAudioSystem *pAudio, const GameSettings &settings, Actions actions, bool paused,
                               std::string location, std::string date)
    : MenuDesignScreen(assets, paused, pAudio), m_actions(std::move(actions)), m_gameData(gameData),
      m_committed(settings), m_draft(settings), m_location(std::move(location)), m_date(std::move(date)),
      m_paused(paused)
{
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
        menuSettingValue(m_draft, setting.id); // An unknown catalog field is an installation error.
        m_settings.push_back(std::move(setting));
    }
    for (const YAML::Node &item : catalog["bindings"])
    {
        const std::string id = item["id"].as<std::string>();
        bool found = false;
        for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
        {
            if (definition.implemented && definition.iniKey == id)
            {
                m_bindings.push_back(
                    {definition.action, id, item["name"].as<std::string>(), item["group"].as<std::string>()});
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
    }
    if (!m_status.empty())
    {
        const Rect status = m_paused ? canvasRect(310, 416, 420, 35) : canvasRect(563.2f, 438, 231.4667f, 28);
        textInRect(status, m_status, "menu_lucida", 11);
    }
}

size_t MainMenuScreen::dirtyCount() const
{
    size_t count = 0;
    for (const Setting &setting : m_settings)
    {
        if (menuSettingValue(m_draft, setting.id) != menuSettingValue(m_committed, setting.id))
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
    return count;
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
                if (m_section == "keyboard")
                {
                    m_draft.keyboard.restoreDefaults(m_draft.controlScheme);
                }
                else
                {
                    for (const Setting &setting : m_settings)
                    {
                        if (setting.section == m_section)
                        {
                            setMenuSettingValue(m_draft, setting.id, menuSettingValue(defaults, setting.id));
                        }
                    }
                    if (m_section == "controls")
                    {
                        m_draft.keyboard.restoreDefaults(m_draft.controlScheme);
                    }
                }
            });
}

void MainMenuScreen::editSetting(const Setting &setting, const std::string &value)
{
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
    float contentHeight = 0;
    for (const std::string &id : m_designLayouts.sortedLayoutIdsForScreenCached(prefix))
    {
        if (id.find("Description") == std::string::npos || id == prefix + "Description")
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
        label(id, pItem->labelText, 0, -m_scroll);
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
        const bool enabled = (setting.depends.empty() || menuSettingValue(m_draft, setting.depends) == "true") &&
                             !(setting.id == "resolution" && m_draft.windowMode == WindowMode::WindowedFullscreen);
        const std::string value = menuSettingValue(m_draft, setting.id);
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
        else
        {
            button(id, rect, "", "text_field", enabled);
            const int amount = std::stoi(value);
            const float fraction = float(amount - setting.minimum) / std::max(1, setting.maximum - setting.minimum);
            const float y = rect.y + rect.height / 2;
            drawSolidRect({rect.x, y - 2, rect.width, 4}, 0xff273629u);
            drawSolidRect({rect.x, y - 2, rect.width * fraction, 4}, 0xff6a93acu);
            drawSolidRect({rect.x + rect.width * fraction - 4, y - 7, 8, 14}, 0xff7bbad8u);
            if (enabled && !modalOpen() && pointerInside(rect) && leftMouseDown())
            {
                const float position = std::clamp((mouseX() - rect.x) / rect.width, 0.0f, 1.0f);
                editSetting(setting, std::to_string(int(std::round(setting.minimum +
                                                                   position * (setting.maximum - setting.minimum)))));
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
    if (reservedMenuBinding(binding))
    {
        setModalBody("That key is reserved. Choose another key.");
        return;
    }
    const KeyboardAction target = *m_capture;
    std::optional<KeyboardAction> conflict;
    for (const Binding &candidate : m_bindings)
    {
        if (candidate.action != target && sameMenuBinding(m_draft.keyboard.binding(candidate.action), binding))
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
            if (!modifierKey && (event.key.mod & (SDL_KMOD_CTRL | SDL_KMOD_ALT | SDL_KMOD_GUI)) != 0)
            {
                setModalBody("Modifier combinations are not supported. Choose a single key.");
                return;
            }
            acceptBinding(keyboardInputBinding(event.key.scancode));
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
