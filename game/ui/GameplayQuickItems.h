#pragma once

#include "game/app/KeyboardBindings.h"

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// The quick items: the potion and scroll buttons on the party frame's end ornaments and their popups
// (level_generation/ui/potion_scroll_popups_20261102), and, with the Quick item rings setting, the ring of the potion
// radial (devdocs/maw/GAPS.md H.6, level_generation/ui/maw_potion_radial_20261025 A).
//
// A popup lists every potion (or scroll) the party carries over the paused game; a click drinks (reads) it as the
// chosen member, exactly as one dropped on their portrait; a right click puts it on one of their six quick slots.
// The ring: a round button at each portrait opens that member's ring of six slots above it (the wheel key the active
// member's); a click uses a slot's potion or scroll, and an empty slot (or a right click) opens a picker beside the
// ring listing every potion and scroll the party carries.
namespace GameplayQuickItems
{
// The buttons at the portraits, the open ring and its picker, over the gameplay HUD.
void renderHud(GameplayScreenRuntime &context, int width, int height);
// Clicks on the buttons and the ring, and the wheel key; true when the frame's click was theirs. `allowInput` is false
// while another screen is over play, which closes the ring; `pointerAllowed` while the pointer is free (not mouse
// look, which the open ring turns off).
bool handleHudInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width, int height,
    bool allowInput, bool pointerAllowed);
// Whether the ring is open (it frees the cursor from mouse look).
bool ringOpen(GameplayScreenRuntime &context);
// Whether the basebar's potion or scroll popup is open: the game pauses under it.
bool popupOpen(GameplayScreenRuntime &context);
// The ring or a popup: the cursor is free (no mouse look) and the world's hover text is hidden.
bool needsCursor(GameplayScreenRuntime &context);
// Whether the ring has the pointer (open, or a click on it still held), so an action bound to a mouse button or the
// wheel (Attack on the left button) must not also act on the world.
bool takesPointerAction(GameplayScreenRuntime &context, KeyboardAction action);
// The same for the left button's own world click.
bool takesPointer(GameplayScreenRuntime &context);
}
}
