#pragma once

#include "game/rules/ClassRules.h"
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
// The danger round the active member, as the party portraits' aggro diamonds tell it: blue in turn-based combat, red
// with a hostile in melee range, yellow within the yellow alert range, else green; unlit while the member cannot act.
// A glow round the portrait and the minimap shows it.
enum class SoloAlert
{
    Unlit,
    Green,
    Yellow,
    Red,
    Blue
};

SoloAlert soloAlert(GameplayScreenRuntime &context, const Character &member, float nearestHostile,
    float engagementRange);
// The unit frame (its portrait in the alert's glow), its buff rows and the action bar's slots.
void renderHud(GameplayScreenRuntime &context, int width, int height, SoloAlert alert);
// The alert's glow: a soft band `band` pixels wide just outside an oval (screen pixels), under or over its rim.
void renderAlertGlow(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &oval, float band,
    SoloAlert alert);
// The two recovery brackets beside the crosshair (centre and the crosshair's scale in pixels per unit).
void renderCrosshairBrackets(GameplayScreenRuntime &context, float centerX, float centerY, float scale);
// A buff tile under the pointer: the party buff or the member's personal buffs, for the buff popups.
std::optional<GameplayHudPointerTarget> buffTargetAt(GameplayScreenRuntime &context, int width, int height, float x,
    float y);
// A tile of the buff and condition rows under a point (screen pixels), for its own popup: which buff (a PartyBuffId,
// a CharacterBuffId, the member's timed potion effect in gameplayPotionEffectLines order, a CharacterCondition, or a
// solo talent's state: 0 Onslaught, 1 Cheat Death) and where it is drawn.
enum class BuffTileKind
{
    Party,
    Character,
    Potion,
    Condition,
    Talent
};

struct BuffTileHit
{
    BuffTileKind kind = BuffTileKind::Party;
    size_t index = 0;
    float remainingSeconds = 0;
    GameplayResolvedHudLayoutElement rect;
};

std::optional<BuffTileHit> buffTileAt(GameplayScreenRuntime &context, int width, int height, float x, float y);
// The class counter's gems over the unit frame's bars (MAW's combo points and Elementalist stacks) under a point
// (screen pixels): the counter, for its popup, and where its gems are drawn.
struct CounterHit
{
    PortraitCounter counter;
    GameplayResolvedHudLayoutElement rect;
};

std::optional<CounterHit> counterAt(GameplayScreenRuntime &context, int width, int height, float x, float y);
// The bar slot (Character::actionBar index, 0-9) whose key (KeyboardAction::ActionBar1-10, the number keys 1-0 by
// default) is held, Shift and Ctrl up; the first held wins.
std::optional<size_t> heldBarSlot(const GameplayInputFrame &input);
// Whether that slot's key went down this frame.
bool barSlotPressed(const GameplayInputFrame &input, size_t slot);
// A bar slot's key as its slot shows it: the bound key's name ("1" to "0" by default).
std::string barKeyName(const GameplayScreenRuntime &context, size_t slot);
// The bar's panel (with its scale) and a slot of keys 1-0 in screen pixels, as drawn; none outside a solo HUD.
std::optional<GameplayResolvedHudLayoutElement> barPanelRect(GameplayScreenRuntime &context, int width, int height);
std::optional<SoloHudRect> barSlotRect(GameplayScreenRuntime &context, int width, int height, size_t slot);
// The slot of keys 1-0 under a point.
std::optional<size_t> barSlotAt(GameplayScreenRuntime &context, int width, int height, float x, float y);
// The filled bar key the right button holds the pointer over in play (its chooser closed), for its inspect popup:
// the spell's, the item's or the weapon's card, or the talent's text (GameplayHudOverlaySupport).
struct BarInspectHit
{
    ActionBarSlot slot;
    GameplayResolvedHudLayoutElement rect;
};

std::optional<BarInspectHit> barInspectAt(GameplayScreenRuntime &context, int width, int height);
// What a bar slot shows as its icon (a spell's, a talent's, the item's or the weapon's), fitted into the box.
void renderSlotIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Character &member,
    const ActionBarSlot &slot, const GameplayObsidianRect &icon, bool dim);
}
}
