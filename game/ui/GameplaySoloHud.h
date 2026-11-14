#pragma once

#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/SoloHudLayout.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class GameplaySpellService;
class GameplayObsidianPainter;
struct GameplayInputFrame;
struct GameplayObsidianRect;

// The solo run's HUD (devdocs/solo_action/HUD.md): the unit frame top left with the buff and debuff rows under it,
// and the action bar in the basebar's panel. It is drawn in place of the party portraits, never on top of them, and
// only while GameplayScreenRuntime::soloHud() holds. Everything is read where it is drawn; nothing polls.
namespace GameplaySoloHud
{
// The unit frame, its buff rows and the action bar's slots, over the frame the party basebar draws.
void renderHud(GameplayScreenRuntime &context, int width, int height);
// The two recovery brackets beside the crosshair (centre and the crosshair's scale in pixels per unit).
void renderCrosshairBrackets(GameplayScreenRuntime &context, float centerX, float centerY, float scale);
// A buff tile under the pointer: the party buff or the member's personal buffs, for the buff popups.
std::optional<GameplayHudPointerTarget> buffTargetAt(GameplayScreenRuntime &context, int width, int height, float x,
    float y);
// The bar slot (Character::actionBar index, 0-9) whose number key 1-0 is held, Shift and Ctrl up; the first held wins.
std::optional<size_t> heldBarSlot(const GameplayInputFrame &input);
// Whether that slot's number key went down this frame.
bool barSlotPressed(const GameplayInputFrame &input, size_t slot);
// A bar slot's key as its slot shows it ("1" to "0").
std::string barKeyName(size_t slot);
// The bar's panel (with its scale) and a slot of keys 1-0 in screen pixels, as drawn; none outside a solo HUD.
std::optional<GameplayResolvedHudLayoutElement> barPanelRect(GameplayScreenRuntime &context, int width, int height);
std::optional<SoloHudRect> barSlotRect(GameplayScreenRuntime &context, int width, int height, size_t slot);
// The slot of keys 1-0 under a point.
std::optional<size_t> barSlotAt(GameplayScreenRuntime &context, int width, int height, float x, float y);
// What a bar slot shows as its icon (a spell's, a talent's, the item's or the weapon's), fitted into the box.
void renderSlotIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Character &member,
    const ActionBarSlot &slot, const GameplayObsidianRect &icon, bool dim);
}
}
