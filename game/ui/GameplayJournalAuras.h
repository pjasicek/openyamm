#pragma once

#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

// The aura panel (MAW, level_generation/ui/maw_aura_panel_20261025 A, "the Ledger"): a full-screen view in the
// Journal's frame, opened from the party buff panels or the Open Auras key instead of a tab. The members' pools, the
// held auras, the chosen aura's reservation, effects and what each member gets of it, from SpellRules::auraReport;
// Release, Move to, Release all and the Spellbook. The renderer and the journal input share the layout below, in the
// JournalAuraPage area.
enum class JournalAuraTargetKind : uint8_t
{
    None,
    // An aura row (its index in the report).
    Aura,
    ReleaseAll,
    Spellbook,
    Release,
    MoveMenu,
    // A member in the open Move-to menu (their index in the party).
    MoveMember,
    // The open Move-to menu, away from its rows: the click keeps it open.
    MoveMenuBody,
};

struct JournalAuraTarget
{
    JournalAuraTargetKind kind = JournalAuraTargetKind::None;
    size_t index = 0;
};

// Whether the game's rules have the aura panel (MAW games).
bool journalHasAuraPanel(const GameplayScreenRuntime &context);
// Opens the Journal on the aura panel, or switches it there.
void openJournalAuraPanel(GameplayScreenRuntime &context);
// A target packed into a journal pointer target's id, and back.
uint32_t packJournalAuraTarget(const JournalAuraTarget &target);
JournalAuraTarget unpackJournalAuraTarget(uint32_t packed);
JournalAuraTarget journalAuraTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y);
// A click on a target: selects an aura, releases, moves (casts as the chosen member), or opens the spellbook.
void activateJournalAuraTarget(
    GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const JournalAuraTarget &target);
// The wheel over the aura list: a positive delta scrolls up.
void scrollJournalAuras(
    const GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    float wheelDelta);
void renderJournalAuras(
    GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float pointerX,
    float pointerY);
}
