#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Mm9HirelingTable;
class Party;
struct Mm9Hireling;
struct Mm9HirelingPassives;

// The MM9 hirelings' dialogue services, wages and passives (devdocs/mm9/MM9_HIRELINGS_PLAN.md phases 7-8;
// research devdocs/mm9/MM9_HIRELINGS.md sections 1.2, 2, 4 and 5).

enum class Mm9HireOutcome : uint8_t
{
    Hired,
    // Already along, or a limit (three hirelings, two paid): MM9 plays the error sound and says nothing.
    Refused,
    // The party lacks the hire fee: the active member's "not enough gold" line.
    NotEnoughGold,
    // The rules keep paid retainers away (ClassRules::paidHirelingRefusal: MAW's Doom and up); its line is shown.
    Declines,
};

// RUDE -10: charges the row's fee (story companions have none), adds the hireling and sets its hire key, which
// MM9 sets in code, not in the RUDE row (cshell@0x10028be8).
Mm9HireOutcome hireMm9Hireling(Party &party, const Mm9Hireling &row);

// RUDE -11: removes the hireling and clears its hire key (MM9's dismiss rows clear it in their own tails), so its
// world body stands at its post again on the next map load. False when it was not along.
bool dismissMm9Hireling(Party &party, const Mm9Hireling &row);

enum class Mm9HirelingServiceOutcome : uint8_t
{
    // Not along, or the row has no service.
    Unavailable,
    // Used less than its cooldown ago: mm9HirelingServiceCooldownText.
    CoolingDown,
    // Ehwaz: the caller opens the Town Portal destination choice (free, no mana); the cooldown is running.
    TownPortal,
    // Sowelu, Florie: every member and hireling at full HP (and Florie's cures).
    Healed,
};

// RUDE -15, the hireling's own service (cshell@0x1002add0), once per the row's cooldown hours after use (the time is
// saved in Mm9PartyHireling::serviceReadyGameMinutes).
Mm9HirelingServiceOutcome useMm9HirelingService(Party &party, const Mm9Hireling &row);
// GAMETEXT:522.
std::string mm9HirelingServiceCooldownText(const std::string &name);

// What the hirelings along give the party, added up; empty without a table or hirelings.
Mm9HirelingPassives mm9PartyHirelingPassives(const Party &party, const Mm9HirelingTable &table);

// The 28-day wages that have come due (each paid retainer from its hire), in MM9's fixed order (object@0x100556c0).
// A wage the purse cannot pay empties it and that retainer leaves (hire key cleared, unlike MM9, whose retainer stayed
// hidden for ever); a member then speaks the "not enough gold" line. MM9's share of found gold is never deducted
// (section 5). Returns the RUDE ids of those who left.
std::vector<uint32_t> payMm9HirelingWages(Party &party, const Mm9HirelingTable &table);
}
