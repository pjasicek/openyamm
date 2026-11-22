#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
// What a ruleset keeps per party (CharacterRulesetState is the same per character); empty under Standard. It is the
// party's own and not the game's, so in a game of several parties (co-op) each has its own, and it travels with the
// party. MAW: its auras, the food held back from it and its deaths. A save of a MAW game holds it inside the
// ruleset's state, where it lay before a game could have more than one party.
struct PartyRulesetState
{
    // The holder of an aura no party member holds (MAW's string holders: Temple, scroll or pedestal).
    static constexpr uint32_t FixedAuraHolder = 0xFFFFFFFFu;

    // The buff auras the party holds (CLASSES_SPELLS_SPEC.md §3): spell id to the holding member's index, or
    // FixedAuraHolder for an aura from a scroll, a pedestal or a temple.
    std::unordered_map<uint32_t, uint32_t> auraHolders;
    // Where each fixed aura came from: the lowercase map file of its scroll or pedestal, which entering another
    // outdoor map ends, or empty for a temple's, which leaving the map ends (SP:2693-2730).
    std::unordered_map<uint32_t, std::string> fixedAuraMaps;
    // A solo run's scroll auras: the game minute each ends, on any map (the user, 2026-11-16). A fixed aura listed
    // here ends only then.
    std::unordered_map<uint32_t, double> fixedAuraEndMinutes;
    // Road to Insanity: the food a dungeon's cap held back, returned on the next outdoor map (vars.refundFood).
    int32_t heldFood = 0;
    // Beyond Madness's death count as of the save, so a save moved to another installation (whose death ledger has no
    // line for the run) keeps its count (vars.MadnessDeathCounter, zzMaw-Monsters.lua:2385-2400).
    int32_t madnessDeaths = 0;

    bool operator==(const PartyRulesetState &) const = default;
};
}
