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
        {InputBindingKind::Keyboard, SDL_SCANCODE_W, 0}, true},
    {KeyboardAction::Backward, "backward", "Backward", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 1,
        {InputBindingKind::Keyboard, SDL_SCANCODE_S, 0}, true},
    {KeyboardAction::Left, "left", "Left", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 2,
        {InputBindingKind::Keyboard, SDL_SCANCODE_A, 0}, true},
    {KeyboardAction::Right, "right", "Right", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 3,
        {InputBindingKind::Keyboard, SDL_SCANCODE_D, 0}, true},
    {KeyboardAction::Yell, "yell", "Yell", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 4,
        {InputBindingKind::Keyboard, SDL_SCANCODE_Y, 0}, true},
    {KeyboardAction::Jump, "jump", "Jump", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 5,
        {InputBindingKind::Keyboard, SDL_SCANCODE_X, 0}, true},
    {KeyboardAction::Combat, "combat", "Combat", KeyboardBindingPage::Page1, KeyboardBindingColumn::Left, 6,
        {InputBindingKind::Keyboard, SDL_SCANCODE_RETURN, 0}, true},
    {KeyboardAction::CastReady, "cast_ready", "Cast Ready", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 0,
        {InputBindingKind::Keyboard, SDL_SCANCODE_Q, 0}, true},
    {KeyboardAction::Attack, "attack", "Attack", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 1,
        {InputBindingKind::Keyboard, SDL_SCANCODE_F, 0}, true},
    {KeyboardAction::Trigger, "trigger", "Trigger", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 2,
        {InputBindingKind::Keyboard, SDL_SCANCODE_SPACE, 0}, true},
    {KeyboardAction::Cast, "cast", "Cast", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 4,
        {InputBindingKind::Keyboard, SDL_SCANCODE_C, 0}, true},
    {KeyboardAction::Pass, "pass", "Pass", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 3,
        {InputBindingKind::Keyboard, SDL_SCANCODE_B, 0}, true},
    {KeyboardAction::CharCycle, "char_cycle", "Char Cycle", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 5,
        {InputBindingKind::Keyboard, SDL_SCANCODE_TAB, 0}, true},
    {KeyboardAction::Quest, "quest", "Quest", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 6,
        {InputBindingKind::Keyboard, SDL_SCANCODE_I, 0}, true},
    {KeyboardAction::QuickRef, "quick_ref", "Quick Ref", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 0,
        {InputBindingKind::Keyboard, SDL_SCANCODE_Z, 0}, true},
    {KeyboardAction::Rest, "rest", "Rest", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 1,
        {InputBindingKind::Keyboard, SDL_SCANCODE_R, 0}, true},
    {KeyboardAction::History, "history", "History", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 2,
        {InputBindingKind::Keyboard, SDL_SCANCODE_H, 0}, true},
    {KeyboardAction::Use, "use", "Use", KeyboardBindingPage::Page1, KeyboardBindingColumn::Right, 3,
        {InputBindingKind::Keyboard, SDL_SCANCODE_E, 0}, true},
    {KeyboardAction::MapBook, "map_book", "Map Book", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 4,
        {InputBindingKind::Keyboard, SDL_SCANCODE_L, 0}, true},
    {KeyboardAction::AlwaysRun, "always_run_toggle", "Always Run", KeyboardBindingPage::Page2,
        KeyboardBindingColumn::Left, 5, {InputBindingKind::Keyboard, SDL_SCANCODE_U, 0}, true},
    {KeyboardAction::LookUp, "look_up", "Look Up", KeyboardBindingPage::Page2, KeyboardBindingColumn::Left, 6,
        {InputBindingKind::Keyboard, SDL_SCANCODE_PAGEDOWN, 0}, true},
    {KeyboardAction::LookDown, "look_down", "Look Down", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 0,
        {InputBindingKind::Keyboard, SDL_SCANCODE_DELETE, 0}, true},
    {KeyboardAction::CenterView, "center_view", "Ctr. View", KeyboardBindingPage::Page2,
        KeyboardBindingColumn::Right, 1, {InputBindingKind::Keyboard, SDL_SCANCODE_END, 0}, true},
    {KeyboardAction::ZoomIn, "zoom_in", "Zoom In", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 2,
        {InputBindingKind::Keyboard, SDL_SCANCODE_KP_PLUS, 0}, true},
    {KeyboardAction::ZoomOut, "zoom_out", "Zoom Out", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 3,
        {InputBindingKind::Keyboard, SDL_SCANCODE_KP_MINUS, 0}, true},
    {KeyboardAction::FlyUp, "fly_up", "Fly Up", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 4,
        {InputBindingKind::Keyboard, SDL_SCANCODE_J, 0}, true},
    {KeyboardAction::FlyDown, "fly_down", "Fly Down", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 5,
        {InputBindingKind::Keyboard, SDL_SCANCODE_K, 0}, true},
    {KeyboardAction::Land, "land", "Land", KeyboardBindingPage::Page2, KeyboardBindingColumn::Right, 6,
        {InputBindingKind::Keyboard, SDL_SCANCODE_HOME, 0}, true},
    {KeyboardAction::DoubleSpeed, "double_speed", "Double Speed", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F2, 0}, true},
    {KeyboardAction::Unstuck, "unstuck", "Unstuck", KeyboardBindingPage::Hidden, KeyboardBindingColumn::Left, 0,
        {}, true},
    {KeyboardAction::OpenWorkbench, "open_workbench", "Open Workbench", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::GatherLoot, "gather_loot", "Gather Loot", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_G, 0}, true},
    {KeyboardAction::AlchemistPick, "alchemist_pick", "Alchemist", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_A, 0}, true},
    {KeyboardAction::SkillCover, "skill_cover", "Cover Switch", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_P, 0}, true},
    {KeyboardAction::SkillManaShield, "skill_mana_shield", "Mana Shield Switch", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_M, 0}, true},
    {KeyboardAction::SkillRotation, "skill_rotation", "Rotation Switch", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_R, 0}, true},
    {KeyboardAction::KnightCharge, "knight_charge", "Knight Charge", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::ShowItemRarity, "show_item_rarity", "Show Item Rarity", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_LALT, 0}, true},
    {KeyboardAction::QuickSpell1, "quick_spell_1", "Quick Spell 1", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F5, 0}, true},
    {KeyboardAction::QuickSpell2, "quick_spell_2", "Quick Spell 2", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F6, 0}, true},
    {KeyboardAction::QuickSpell3, "quick_spell_3", "Quick Spell 3", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F7, 0}, true},
    {KeyboardAction::QuickSpell4, "quick_spell_4", "Quick Spell 4", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F8, 0}, true},
    {KeyboardAction::FollowerPanel, "follower_panel", "Follower Panel", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_0, 0}, true},
    {KeyboardAction::Follower1, "follower_1", "Follower 1", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_6, 0}, true},
    {KeyboardAction::Follower2, "follower_2", "Follower 2", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_7, 0}, true},
    {KeyboardAction::Follower3, "follower_3", "Follower 3", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_8, 0}, true},
    {KeyboardAction::Follower4, "follower_4", "Follower 4", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_9, 0}, true},
    {KeyboardAction::Bag1, "bag_1", "Bag 1", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_1, 0}, true},
    {KeyboardAction::Bag2, "bag_2", "Bag 2", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_2, 0}, true},
    {KeyboardAction::Bag3, "bag_3", "Bag 3", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_3, 0}, true},
    {KeyboardAction::Bag4, "bag_4", "Bag 4", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_4, 0}, true},
    {KeyboardAction::CraftingBag, "crafting_bag", "Crafting Bag", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_B, 0}, true},
    {KeyboardAction::OpenProgress, "open_progress", "Open Progress", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::OpenAuras, "open_auras", "Open Auras", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickItemWheel, "quick_item_wheel", "Potions", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_V, 0}, true},
    {KeyboardAction::ScrollPopup, "scroll_popup", "Scrolls", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_T, 0}, true},
    // One quick-use key for the active member's first slot; the other slots are bound on demand (user, 2026-10-25).
    {KeyboardAction::QuickItem1, "quick_item_1", "Quick Potion (Slot 1)", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_N, 0}, true},
    {KeyboardAction::QuickItem2, "quick_item_2", "Potion Slot 2", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickItem3, "quick_item_3", "Potion Slot 3", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickItem4, "quick_item_4", "Potion Slot 4", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickItem5, "quick_item_5", "Potion Slot 5", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickItem6, "quick_item_6", "Potion Slot 6", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {}, true},
    {KeyboardAction::QuickSave, "quick_save", "Quick Save", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F9, 0}, true},
    {KeyboardAction::QuickLoad, "quick_load", "Quick Load", KeyboardBindingPage::Hidden,
        KeyboardBindingColumn::Left, 0, {InputBindingKind::Keyboard, SDL_SCANCODE_F10, 0}, true},
}};

const std::array<KeyboardScancodeName, 97> KeyboardScancodeNames = {{
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
    {SDL_SCANCODE_KP_1, "Num 1"},
    {SDL_SCANCODE_KP_2, "Num 2"},
    {SDL_SCANCODE_KP_3, "Num 3"},
    {SDL_SCANCODE_KP_4, "Num 4"},
    {SDL_SCANCODE_KP_5, "Num 5"},
    {SDL_SCANCODE_KP_6, "Num 6"},
    {SDL_SCANCODE_KP_7, "Num 7"},
    {SDL_SCANCODE_KP_8, "Num 8"},
    {SDL_SCANCODE_KP_9, "Num 9"},
    {SDL_SCANCODE_KP_0, "Num 0"},
    {SDL_SCANCODE_KP_MULTIPLY, "Multiply"},
    {SDL_SCANCODE_KP_DIVIDE, "Divide"},
    {SDL_SCANCODE_KP_PERIOD, "Decimal"},
    {SDL_SCANCODE_KP_ENTER, "Num Enter"},
    {SDL_SCANCODE_KP_MINUS, "Subtract"},
    {SDL_SCANCODE_BACKSPACE, "Backspace"},
    {SDL_SCANCODE_CAPSLOCK, "Caps_Lock"},
    {SDL_SCANCODE_GRAVE, "Grave"},
    {SDL_SCANCODE_MINUS, "Minus"},
    {SDL_SCANCODE_EQUALS, "Equals"},
    {SDL_SCANCODE_LEFTBRACKET, "Left_Bracket"},
    {SDL_SCANCODE_RIGHTBRACKET, "Right_Bracket"},
    {SDL_SCANCODE_BACKSLASH, "Backslash"},
    {SDL_SCANCODE_SEMICOLON, "Semicolon"},
    {SDL_SCANCODE_APOSTROPHE, "Apostrophe"},
    {SDL_SCANCODE_COMMA, "Comma"},
    {SDL_SCANCODE_PERIOD, "Period"},
    {SDL_SCANCODE_SLASH, "Slash"},
    {SDL_SCANCODE_F1, "F1"},
    {SDL_SCANCODE_F2, "F2"},
    {SDL_SCANCODE_F3, "F3"},
    {SDL_SCANCODE_F4, "F4"},
    {SDL_SCANCODE_F5, "F5"},
    {SDL_SCANCODE_F6, "F6"},
    {SDL_SCANCODE_F7, "F7"},
    {SDL_SCANCODE_F8, "F8"},
    {SDL_SCANCODE_F9, "F9"},
    {SDL_SCANCODE_F10, "F10"},
    {SDL_SCANCODE_F11, "F11"},
    {SDL_SCANCODE_F12, "F12"},
    {SDL_SCANCODE_LALT, "Left_Alt"},
    {SDL_SCANCODE_RALT, "Right_Alt"},
    {SDL_SCANCODE_LCTRL, "Left_Ctrl"},
    {SDL_SCANCODE_RCTRL, "Right_Ctrl"},
    {SDL_SCANCODE_LSHIFT, "Left_Shift"},
    {SDL_SCANCODE_RSHIFT, "Right_Shift"},
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

// Parses "<prefix><number>" (e.g. "mousebutton5" or "mouse5") into an SDL mouse button index, or 0 when invalid.
uint8_t parseMouseButtonNumber(const std::string &normalized, std::string_view prefix)
{
    if (normalized.size() <= prefix.size() || normalized.compare(0, prefix.size(), prefix) != 0)
    {
        return 0;
    }

    const std::string numeric = normalized.substr(prefix.size());
    char *pEnd = nullptr;
    const long parsed = std::strtol(numeric.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0' || parsed < 1 || parsed > MaxBindableMouseButton)
    {
        return 0;
    }

    return static_cast<uint8_t>(parsed);
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

InputBinding keyboardInputBinding(SDL_Scancode scancode)
{
    if (scancode == SDL_SCANCODE_UNKNOWN)
    {
        return {};
    }

    return InputBinding{InputBindingKind::Keyboard, scancode, 0};
}

InputBinding mouseButtonInputBinding(uint8_t button)
{
    return InputBinding{InputBindingKind::MouseButton, SDL_SCANCODE_UNKNOWN, button};
}

bool mouseButtonHeldInFlags(SDL_MouseButtonFlags flags, uint8_t button)
{
    return button >= 1 && button <= MaxBindableMouseButton && (flags & SDL_BUTTON_MASK(button)) != 0;
}

InputBinding mouseWheelInputBinding(float delta)
{
    if (delta > 0.0f)
    {
        return InputBinding{InputBindingKind::MouseWheelUp};
    }
    if (delta < 0.0f)
    {
        return InputBinding{InputBindingKind::MouseWheelDown};
    }
    return {};
}

std::array<InputBinding, KeyboardActionCount> createDefaultKeyboardBindings()
{
    std::array<InputBinding, KeyboardActionCount> bindings = {};

    for (const KeyboardBindingDefinition &definition : KeyboardBindings)
    {
        bindings[keyboardActionIndex(definition.action)] = definition.defaultBinding;
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

InputBinding parseInputBindingName(const std::string &name)
{
    if (name.empty())
    {
        return {};
    }

    const std::string normalized = normalizeBindingName(name);

    if (normalized == "mouseleft" || normalized == "leftmouse" || normalized == "lmb")
    {
        return mouseButtonInputBinding(SDL_BUTTON_LEFT);
    }

    if (normalized == "mousewheelup" || normalized == "wheelup")
    {
        return mouseWheelInputBinding(1.0f);
    }
    if (normalized == "mousewheeldown" || normalized == "wheeldown")
    {
        return mouseWheelInputBinding(-1.0f);
    }

    // "MouseButton_N" is the saved form; "Mouse N" is the display form.
    uint8_t mouseButton = parseMouseButtonNumber(normalized, "mousebutton");

    if (mouseButton == 0)
    {
        mouseButton = parseMouseButtonNumber(normalized, "mouse");
    }

    if (mouseButton != 0)
    {
        return mouseButtonInputBinding(mouseButton);
    }

    const SDL_Scancode scancode = parseKeyboardBindingName(name);

    if (scancode != SDL_SCANCODE_UNKNOWN)
    {
        return keyboardInputBinding(scancode);
    }

    return {};
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
    static const std::array<std::string, SDL_SCANCODE_COUNT> DisplayNames =
        []()
        {
            std::array<std::string, SDL_SCANCODE_COUNT> names = {};

            for (size_t index = 0; index < names.size(); ++index)
            {
                names[index] = keyboardBindingName(static_cast<SDL_Scancode>(index));
            }

            return names;
        }();

    if (scancode >= 0 && static_cast<size_t>(scancode) < DisplayNames.size())
    {
        return DisplayNames[static_cast<size_t>(scancode)];
    }

    return keyboardBindingName(scancode);
}

std::string inputBindingName(const InputBinding &binding)
{
    switch (binding.kind)
    {
    case InputBindingKind::Keyboard:
        return keyboardBindingName(binding.scancode);

    case InputBindingKind::MouseWheelUp:
        return "MouseWheelUp";

    case InputBindingKind::MouseWheelDown:
        return "MouseWheelDown";

    case InputBindingKind::MouseButton:
        if (binding.mouseButton == SDL_BUTTON_LEFT)
        {
            return "MouseLeft";
        }
        return "MouseButton_" + std::to_string(static_cast<int>(binding.mouseButton));

    case InputBindingKind::None:
    default:
        return "Unbound";
    }
}

std::string inputBindingDisplayName(const InputBinding &binding)
{
    switch (binding.kind)
    {
    case InputBindingKind::Keyboard:
        return keyboardBindingDisplayName(binding.scancode);

    case InputBindingKind::MouseWheelUp:
        return "Wheel Up";

    case InputBindingKind::MouseWheelDown:
        return "Wheel Down";

    case InputBindingKind::MouseButton:
        if (binding.mouseButton == SDL_BUTTON_LEFT)
        {
            return "LMB";
        }
        return "Mouse " + std::to_string(static_cast<int>(binding.mouseButton));

    case InputBindingKind::None:
    default:
        return "Unbound";
    }
}
}
