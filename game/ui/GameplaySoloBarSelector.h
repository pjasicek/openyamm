#pragma once

#include "game/app/KeyboardBindings.h"

#include <cstddef>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// The solo action bar's slot selector (devdocs/solo_action/HUD.md "Slot selector"): Ctrl and a bar key, or a Ctrl
// click on a slot, opens a window beside the bar listing what the member can put on that key: known spells, learned
// active talents, the potions and scrolls carried and the weapon actions, with a search field and category tabs.
// A click puts the chosen thing on the key (moving it from another key); the game is paused while it is open, and
// the list is built when it opens (filtered again on a tab or search change), never polled.
namespace GameplaySoloBarSelector
{
bool isOpen(const GameplayScreenRuntime &context);
// Opens it for a slot of keys 1-0 of the active member's bar; nothing outside a solo HUD.
void open(GameplayScreenRuntime &context, size_t slot);
void close(GameplayScreenRuntime &context);
// Whether Ctrl is held over plain gameplay with the selector closed: the game pauses and the bar's keys are lit.
bool armed(const GameplayScreenRuntime &context);
// Ends that state (Ctrl let go elsewhere, another screen opened).
void disarm(GameplayScreenRuntime &context);
// Whether it has the pointer (open, or the click that closed it still held): the world must not take the click.
bool takesPointer(const GameplayScreenRuntime &context);
// The same for an action bound to a mouse button (Attack on the left button).
bool takesPointerAction(const GameplayScreenRuntime &context, KeyboardAction action);

// On plain gameplay with the bar shown: holding Ctrl arms the bar (see armed); Ctrl and a bar key, or a Ctrl click on
// a slot, opens the selector. Not while an action is bound to that Ctrl key, nor while the debug turbo movement (Ctrl)
// moves the party. True when the frame's click was its own. `allowed` is false while anything else is open;
// `pointerAllowed` while the cursor is free.
bool handleBarInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width, int height,
    bool allowed, bool pointerAllowed);
// The open window's keys, typing, wheel and clicks (the game is paused under it).
void handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width, int height);
// The window beside the bar, or the lit keys while armed, over the HUD.
void render(GameplayScreenRuntime &context, int width, int height);
// The status line's text for a bar slot under the free pointer (how to open the selector), or empty.
std::string barHoverText(GameplayScreenRuntime &context, int width, int height, float x, float y);
}
}
