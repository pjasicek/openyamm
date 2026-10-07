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
    Hidden = 0,
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
    Use,
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
    DoubleSpeed,
    Count
};

constexpr size_t KeyboardActionCount = static_cast<size_t>(KeyboardAction::Count);

enum class InputBindingKind : uint8_t
{
    None = 0,
    Keyboard,
    MouseButton,
    MouseWheelUp,
    MouseWheelDown
};

struct InputBinding
{
    InputBindingKind kind = InputBindingKind::None;
    SDL_Scancode scancode = SDL_SCANCODE_UNKNOWN;
    uint8_t mouseButton = 0;
};

struct KeyboardBindingDefinition
{
    KeyboardAction action = KeyboardAction::Forward;
    std::string_view iniKey;
    std::string_view label;
    KeyboardBindingPage page = KeyboardBindingPage::Page1;
    KeyboardBindingColumn column = KeyboardBindingColumn::Left;
    size_t row = 0;
    InputBinding defaultBinding = {};
    bool implemented = false;
};

size_t keyboardActionIndex(KeyboardAction action);
const std::array<KeyboardBindingDefinition, KeyboardActionCount> &keyboardBindingDefinitions();
const KeyboardBindingDefinition &keyboardBindingDefinition(KeyboardAction action);
InputBinding keyboardInputBinding(SDL_Scancode scancode);
InputBinding mouseButtonInputBinding(uint8_t button);
InputBinding mouseWheelInputBinding(float delta);
std::array<InputBinding, KeyboardActionCount> createDefaultKeyboardBindings();
SDL_Scancode parseKeyboardBindingName(const std::string &name);
InputBinding parseInputBindingName(const std::string &name);
std::string keyboardBindingName(SDL_Scancode scancode);
std::string keyboardBindingDisplayName(SDL_Scancode scancode);
std::string inputBindingName(const InputBinding &binding);
std::string inputBindingDisplayName(const InputBinding &binding);
}
