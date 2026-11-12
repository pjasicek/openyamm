#pragma once

#include "game/party/BattleOrders.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class Party;
class SpellTable;
struct SpellEntry;
struct Character;
struct GameplayInputFrame;

// The Battle Orders window (devdocs/BATTLE_ORDERS.md; the chosen study level_generation/ui/combat_orders_20261108,
// layout A): each member's attack orders with their conditions, the fallback, the upkeep list (the spells the Upkeep
// key keeps up) and the quick keys (Quick Cast, Quick Spell 1-4), over the open spellbook. Opened by the spellbook's
// Battle Orders button or the Battle Orders key (which opens the book with it). Also the spellbook's short spell
// menu: a right click on a spell assigns it.
namespace GameplayBattleOrders
{
// A right click on a spell up to this long opens its menu; held longer, the spell's description shows instead.
constexpr uint64_t SpellMenuClickMilliseconds = 300;

enum class Preset
{
    Fighter,
    Archer,
    Caster,
    Healer,
};

bool isOpen(const GameplayScreenRuntime &context);
// Opens the window on the active member, over the open spellbook.
void open(GameplayScreenRuntime &context, bool closesBook);
// Closes the window, and the book when the window was opened with it.
void close(GameplayScreenRuntime &context);
void render(GameplayScreenRuntime &context, int width, int height);
void handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input);

bool spellMenuOpen(const GameplayScreenRuntime &context);
void openSpellMenu(GameplayScreenRuntime &context, uint32_t spellId, float x, float y);
void closeSpellMenu(GameplayScreenRuntime &context);
void renderSpellMenu(GameplayScreenRuntime &context, int width, int height);
void handleSpellMenuInput(GameplayScreenRuntime &context, const GameplayInputFrame &input);

// Puts a spell on Quick Cast (slot 0) or Quick Spell 1-4 (slots 1-4) of a member, or clears the slot (nullptr), and
// says so: the window's quick keys, the spell menu and the spellbook's Quick Cast button.
void assignQuickSlot(GameplayScreenRuntime &context, size_t memberIndex, size_t slot, const SpellEntry *pSpell);
// The spellbook's Attack Spell button, for players who want no more than one attack spell: the member's orders become
// that spell alone (setAttackSpell), replacing any plan; nullptr clears the orders back to the weapon.
void assignAttackSpell(GameplayScreenRuntime &context, size_t memberIndex, const SpellEntry *pSpell);

// The Quick Reference's Orders row: each member's orders that are on as small spell icons in order, the fallback's
// mark last; pointing at a member's cell lists the orders with their conditions and the quick keys.
void renderQuickReferenceOrders(GameplayScreenRuntime &context, int width, int height);

// A starting plan for the member from the spells they know: Fighter has no orders (the weapon); Archer shoots beyond
// melee reach; Caster casts their strongest known single-target attack spell; Healer heals an ally below half HP and
// cures, holding otherwise.
void applyPreset(Character &member, const SpellTable &spellTable, Preset preset);
// Another member's orders and fallback, without the spell orders this member cannot cast.
void copyOrders(Character &member, const Character &source, const SpellTable &spellTable);

enum class UpkeepPreset
{
    Buffs,
    Healing,
};

// Adds to the member's upkeep list what it lacks of a kind, up to the limit. Buffs: the lasting buffs the member
// knows, the strongest first, without those a known wider spell already gives (Day of Protection's resistances, Hour
// of Power's Heroism), each renewed from the default time left on; Torch Light indoors only. Healing: Heal for an
// ally below 90 % HP, then the cures. Returns how many it added.
size_t addUpkeepPreset(Character &member, const Party &party, const SpellTable &spellTable, UpkeepPreset preset);
// Another member's upkeep list, without the spells this member cannot cast.
void copyUpkeep(Character &member, const Character &source, const Party &party, const SpellTable &spellTable);
}
}
