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
    // MAW's keys (devdocs/maw/GAPS.md §11 D.18), listed only in a MAW game: lift a stuck party, open the Workbench,
    // gather corpses and crafting items, and on the inventory and skills pages the alchemist pick and the switches;
    // a lone Knight's charge at the monster under the cursor.
    Unstuck,
    OpenWorkbench,
    GatherLoot,
    AlchemistPick,
    SkillCover,
    SkillManaShield,
    SkillRotation,
    KnightCharge,
    // Held: items glow in their rarity colour (the gameplay.rarity_glow setting "hold").
    ShowItemRarity,
    // MMMerge's four extra quick spells (ExtraQuickSpells.lua): cast the active member's slot, else attack.
    QuickSpell1,
    QuickSpell2,
    QuickSpell3,
    QuickSpell4,
    // MMMerge's follower keys (NPCFollowers.lua:345-351): toggle the follower panel, speak with follower 1-4.
    FollowerPanel,
    Follower1,
    Follower2,
    Follower3,
    Follower4,
    // MAW's multibag on the inventory page and a shop's or chest's inventory: open (and zoom) bag 1-4
    // (zzMaw-MultiBag.lua:38-67); with Shift the number keys still select party members.
    Bag1,
    Bag2,
    Bag3,
    Bag4,
    // MAW's crafting bag (zzzMaw_CraftingBag.lua:49-55): with Shift, tags or untags the open bag on the inventory page.
    CraftingBag,
    // MAW: opens the Journal on its Progress tab (unbound by default).
    OpenProgress,
    // MAW: opens the aura panel (unbound by default).
    OpenAuras,
    // The potion radial (GAPS.md H.6): the active member's ring (with the quick item rings on; else the basebar's potion
    // popup), the basebar's scroll popup, and each of the six quick slots.
    QuickItemWheel,
    ScrollPopup,
    QuickItem1,
    QuickItem2,
    QuickItem3,
    QuickItem4,
    QuickItem5,
    QuickItem6,
    QuickSave,
    QuickLoad,
    Count
};

constexpr size_t KeyboardActionCount = static_cast<size_t>(KeyboardAction::Count);

// SDL reports mouse button state as a 32-bit mask, so button indices 1..32 can be bound.
constexpr uint8_t MaxBindableMouseButton = 32;

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
// True when the SDL mouse button state flags report the given button (1-based SDL index, including X1/X2) held.
bool mouseButtonHeldInFlags(SDL_MouseButtonFlags flags, uint8_t button);
InputBinding mouseWheelInputBinding(float delta);
std::array<InputBinding, KeyboardActionCount> createDefaultKeyboardBindings();
SDL_Scancode parseKeyboardBindingName(const std::string &name);
InputBinding parseInputBindingName(const std::string &name);
std::string keyboardBindingName(SDL_Scancode scancode);
std::string keyboardBindingDisplayName(SDL_Scancode scancode);
std::string inputBindingName(const InputBinding &binding);
std::string inputBindingDisplayName(const InputBinding &binding);
}
