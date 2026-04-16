#pragma once

#include <SDL3/SDL.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace OpenYAMM::Game
{
enum class KeyboardBindingPage : uint8_t
{
    Page1 = 1,
    Page2 = 2
};

enum class KeyboardBindingColumn : uint8_t
{
    Left = 0,
    Right = 1
};

enum class KeyboardAction : uint8_t
{
    Forward = 0,
    Backward,
    Left,
    Right,
    Yell,
    Jump,
    Combat,
    CastReady,
    Attack,
    Trigger,
    Cast,
    Pass,
    CharCycle,
    Quest,
    QuickRef,
    Rest,
    History,
    AutoNotes,
    MapBook,
    AlwaysRun,
    LookUp,
    LookDown,
    CenterView,
    ZoomIn,
    ZoomOut,
    FlyUp,
    FlyDown,
    Land,
    Count
};

constexpr size_t KeyboardActionCount = static_cast<size_t>(KeyboardAction::Count);

struct KeyboardBindingDefinition
{
    KeyboardAction action = KeyboardAction::Forward;
    std::string_view iniKey;
    std::string_view label;
    KeyboardBindingPage page = KeyboardBindingPage::Page1;
    KeyboardBindingColumn column = KeyboardBindingColumn::Left;
    size_t row = 0;
    SDL_Scancode defaultScancode = SDL_SCANCODE_UNKNOWN;
    bool implemented = false;
};

size_t keyboardActionIndex(KeyboardAction action);
const std::array<KeyboardBindingDefinition, KeyboardActionCount> &keyboardBindingDefinitions();
const KeyboardBindingDefinition &keyboardBindingDefinition(KeyboardAction action);
std::array<SDL_Scancode, KeyboardActionCount> createDefaultKeyboardBindings();
SDL_Scancode parseKeyboardBindingName(const std::string &name);
std::string keyboardBindingName(SDL_Scancode scancode);
std::string keyboardBindingDisplayName(SDL_Scancode scancode);
}
