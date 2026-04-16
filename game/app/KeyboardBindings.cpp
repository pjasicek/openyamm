#include "game/app/KeyboardBindings.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
struct KeyboardScancodeName
{
    SDL_Scancode scancode = SDL_SCANCODE_UNKNOWN;
    const char *pName = "";
};

const std::array<KeyboardBindingDefinition, KeyboardActionCount> KeyboardBindings = {{
    {KeyboardAction::Forward, "forward", "Forward", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 0,
        SDL_SCANCODE_W, true},
    {KeyboardAction::Backward, "backward", "Backward", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 1,
        SDL_SCANCODE_S, true},
    {KeyboardAction::Left, "left", "Left", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 2,
        SDL_SCANCODE_A, true},
    {KeyboardAction::Right, "right", "Right", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 3,
        SDL_SCANCODE_D, true},
    {KeyboardAction::Yell, "yell", "Yell", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 4,
        SDL_SCANCODE_Y, false},
    {KeyboardAction::Jump, "jump", "Jump", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 5,
        SDL_SCANCODE_X, true},
    {KeyboardAction::Combat, "combat", "Combat", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 6,
        SDL_SCANCODE_RETURN, false},
    {KeyboardAction::CastReady, "cast_ready", "Cast Ready", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 0,
        SDL_SCANCODE_Q, true},
    {KeyboardAction::Attack, "attack", "Attack", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 1,
        SDL_SCANCODE_F, true},
    {KeyboardAction::Trigger, "trigger", "Trigger", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 2,
        SDL_SCANCODE_SPACE, true},
    {KeyboardAction::Cast, "cast", "Cast", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 3,
        SDL_SCANCODE_C, true},
    {KeyboardAction::Pass, "pass", "Pass", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 4,
        SDL_SCANCODE_B, false},
    {KeyboardAction::CharCycle, "char_cycle", "Char Cycle", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 5,
        SDL_SCANCODE_TAB, true},
    {KeyboardAction::Quest, "quest", "Quest", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 6,
        SDL_SCANCODE_I, true},
    {KeyboardAction::QuickRef, "quick_ref", "Quick Ref", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 0,
        SDL_SCANCODE_Z, false},
    {KeyboardAction::Rest, "rest", "Rest", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 1,
        SDL_SCANCODE_R, true},
    {KeyboardAction::History, "history", "History", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 2,
        SDL_SCANCODE_H, true},
    {KeyboardAction::AutoNotes, "auto_notes", "Auto Notes", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 3,
        SDL_SCANCODE_N, true},
    {KeyboardAction::MapBook, "map_book", "Map Book", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 4,
        SDL_SCANCODE_L, true},
    {KeyboardAction::AlwaysRun, "always_run_toggle", "Always Run", KeyboardBindingPage::Page2,
        KeyboardBindingColumn::Left, 5, SDL_SCANCODE_U, true},
    {KeyboardAction::LookUp, "look_up", "Look Up", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 6,
        SDL_SCANCODE_PAGEDOWN, true},
    {KeyboardAction::LookDown, "look_down", "Look Down", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 0,
        SDL_SCANCODE_DELETE, true},
    {KeyboardAction::CenterView, "center_view", "Ctr. View", KeyboardBindingPage::Page2,
        KeyboardBindingColumn::Right, 1, SDL_SCANCODE_END, true},
    {KeyboardAction::ZoomIn, "zoom_in", "Zoom In", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 2,
        SDL_SCANCODE_KP_PLUS, true},
    {KeyboardAction::ZoomOut, "zoom_out", "Zoom Out", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 3,
        SDL_SCANCODE_KP_MINUS, true},
    {KeyboardAction::FlyUp, "fly_up", "Fly Up", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 4,
        SDL_SCANCODE_J, true},
    {KeyboardAction::FlyDown, "fly_down", "Fly Down", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 5,
        SDL_SCANCODE_K, true},
    {KeyboardAction::Land, "land", "Land", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 6,
        SDL_SCANCODE_HOME, true},
}};

const std::array<KeyboardScancodeName, 53> KeyboardScancodeNames = {{
    {SDL_SCANCODE_A, "A"},
    {SDL_SCANCODE_B, "B"},
    {SDL_SCANCODE_C, "C"},
    {SDL_SCANCODE_D, "D"},
    {SDL_SCANCODE_E, "E"},
    {SDL_SCANCODE_F, "F"},
    {SDL_SCANCODE_G, "G"},
    {SDL_SCANCODE_H, "H"},
    {SDL_SCANCODE_I, "I"},
    {SDL_SCANCODE_J, "J"},
    {SDL_SCANCODE_K, "K"},
    {SDL_SCANCODE_L, "L"},
    {SDL_SCANCODE_M, "M"},
    {SDL_SCANCODE_N, "N"},
    {SDL_SCANCODE_O, "O"},
    {SDL_SCANCODE_P, "P"},
    {SDL_SCANCODE_Q, "Q"},
    {SDL_SCANCODE_R, "R"},
    {SDL_SCANCODE_S, "S"},
    {SDL_SCANCODE_T, "T"},
    {SDL_SCANCODE_U, "U"},
    {SDL_SCANCODE_V, "V"},
    {SDL_SCANCODE_W, "W"},
    {SDL_SCANCODE_X, "X"},
    {SDL_SCANCODE_Y, "Y"},
    {SDL_SCANCODE_Z, "Z"},
    {SDL_SCANCODE_0, "0"},
    {SDL_SCANCODE_1, "1"},
    {SDL_SCANCODE_2, "2"},
    {SDL_SCANCODE_3, "3"},
    {SDL_SCANCODE_4, "4"},
    {SDL_SCANCODE_5, "5"},
    {SDL_SCANCODE_6, "6"},
    {SDL_SCANCODE_7, "7"},
    {SDL_SCANCODE_8, "8"},
    {SDL_SCANCODE_9, "9"},
    {SDL_SCANCODE_SPACE, "Space"},
    {SDL_SCANCODE_RETURN, "Return"},
    {SDL_SCANCODE_TAB, "Tab"},
    {SDL_SCANCODE_ESCAPE, "Escape"},
    {SDL_SCANCODE_DELETE, "Delete"},
    {SDL_SCANCODE_HOME, "Home"},
    {SDL_SCANCODE_END, "End"},
    {SDL_SCANCODE_PAGEUP, "Page_Up"},
    {SDL_SCANCODE_PAGEDOWN, "Page_Down"},
    {SDL_SCANCODE_INSERT, "Insert"},
    {SDL_SCANCODE_UP, "Up"},
    {SDL_SCANCODE_DOWN, "Down"},
    {SDL_SCANCODE_LEFT, "Left"},
    {SDL_SCANCODE_RIGHT, "Right"},
    {SDL_SCANCODE_KP_PLUS, "Add"},
    {SDL_SCANCODE_KP_MINUS, "Subtract"},
    {SDL_SCANCODE_BACKSPACE, "Backspace"},
}};

std::string normalizeBindingName(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        if (character == ' ' || character == '-' || character == '_')
        {
            continue;
        }

        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}
}

size_t keyboardActionIndex(KeyboardAction action)
{
    return static_cast<size_t>(action);
}

const std::array<KeyboardBindingDefinition, KeyboardActionCount> &keyboardBindingDefinitions()
{
    return KeyboardBindings;
}

const KeyboardBindingDefinition &keyboardBindingDefinition(KeyboardAction action)
{
    return KeyboardBindings[keyboardActionIndex(action)];
}

std::array<SDL_Scancode, KeyboardActionCount> createDefaultKeyboardBindings()
{
    std::array<SDL_Scancode, KeyboardActionCount> bindings = {};

    for (const KeyboardBindingDefinition &definition : KeyboardBindings)
    {
        bindings[keyboardActionIndex(definition.action)] = definition.defaultScancode;
    }

    return bindings;
}

SDL_Scancode parseKeyboardBindingName(const std::string &name)
{
    if (name.empty())
    {
        return SDL_SCANCODE_UNKNOWN;
    }

    const std::string normalized = normalizeBindingName(name);

    for (const KeyboardScancodeName &entry : KeyboardScancodeNames)
    {
        if (normalizeBindingName(entry.pName) == normalized)
        {
            return entry.scancode;
        }
    }

    if (normalized.rfind("scancode", 0) == 0 && normalized.size() > 8)
    {
        const std::string numeric = normalized.substr(8);
        char *pEnd = nullptr;
        const long parsed = std::strtol(numeric.c_str(), &pEnd, 10);

        if (pEnd != nullptr && *pEnd == '\0' && parsed >= 0 && parsed < SDL_SCANCODE_COUNT)
        {
            return static_cast<SDL_Scancode>(parsed);
        }
    }

    return SDL_SCANCODE_UNKNOWN;
}

std::string keyboardBindingName(SDL_Scancode scancode)
{
    for (const KeyboardScancodeName &entry : KeyboardScancodeNames)
    {
        if (entry.scancode == scancode)
        {
            return entry.pName;
        }
    }

    if (scancode == SDL_SCANCODE_UNKNOWN)
    {
        return "Unbound";
    }

    return "Scancode_" + std::to_string(static_cast<int>(scancode));
}

std::string keyboardBindingDisplayName(SDL_Scancode scancode)
{
    return keyboardBindingName(scancode);
}
}
