#pragma once

#include "game/content/RulesetOptions.h"
#include "game/party/Party.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// A guest's character has two writers. Its player's own game does what the player does with it (blows and their
// recovery, potions, the bags, skill points) on its copy and sends the result; the host does what the world does to
// it (a monster's hit, a reward, loot, another player's heal). This puts a result the guest's game sent together with
// what the host's world did meanwhile.
//
// base is the character as the guest's game last had it from the host, host as the host has it now, put as the
// guest's game has it now. The answer is put, with the world's part of the difference between base and host:
//   - hit points, spell points, experience, skill points, gold, bank gold and food take the host's change on top;
//   - a condition, a buff or an award the host changed is the host's;
//   - if the host changed what the character carries or wears, all of that is the host's, as are the level, the class
//     and the stats when the host changed them (a promotion, an event);
//   - what the ruleset keeps for the party (PartyRulesetState): its auras are the host's when the host changed them;
//   - everything else is the guest's.
// The campaign is not part of it: the answer's is put's, which the caller leaves out.
Party::Snapshot mergeGuestCharacter(
    const Party::Snapshot &base,
    const Party::Snapshot &host,
    const Party::Snapshot &put);

// The first thing in which a joining game's content differs from the host's (GameApplication::coopContentIdentity),
// worded for the player who is refused; nothing when the two are alike.
std::optional<std::string> coopContentDifference(
    const std::vector<std::string> &host,
    const std::vector<std::string> &guest);

// The rules a game plays by as a session advertises them and a joining game names them: the ruleset's id and, for a
// ruleset package (MAW), its difficulty, its challenge mode and whether it is a solo run ("maw nightmare solo").
// Standard rules are its id alone.
std::string coopRulesText(const RulesetSelection &ruleset);

// Why a game of `guest` rules does not join a host of `host` rules (both coopRulesText); nothing when it does.
// The world is the host's, so a guest plays by the host's difficulty, progression and challenge mode for the session,
// whatever its own game's are, Nightmare included (as in MAW's own multiplayer; the user, 2026-11-21: "it's co-op,
// let them do whatever"). What must be the same:
//   - the ruleset;
//   - under a ruleset package, the kind: a solo run or a party (the solo run is a rule of the whole world there).
std::optional<std::string> coopRulesRefusal(const std::string &host, const std::string &guest);

// A party's own state as two games exchange it: without the campaign, which travels by itself, and without what the
// members' portraits show at the moment, which is each game's own.
Party::Snapshot characterForWire(Party::Snapshot party);

// What of a character changes all the time while the world runs: hit points, spell points, the recovery and how long
// each buff has left. The host sends these alone, many times a second, and the whole character only when something
// else changed.
struct CharacterVitals
{
    struct Member
    {
        int32_t health = 0;
        int32_t spellPoints = 0;
        float recoverySecondsRemaining = 0.0f;

        bool operator==(const Member &) const = default;
    };

    std::vector<Member> members;
    std::array<float, PartyBuffCount> partyBuffSeconds = {};
    std::vector<float> characterBuffSeconds;
    float itemEffectElapsedGameSeconds = 0.0f;

    bool operator==(const CharacterVitals &) const = default;
};

CharacterVitals takeCharacterVitals(const Party::Snapshot &party);
// The party with its vitals set to nothing: two parties that differ in vitals alone are then the same.
Party::Snapshot withoutCharacterVitals(Party::Snapshot party);
// False when the vitals are of a party of another shape.
bool applyCharacterVitals(Party::Snapshot &party, const CharacterVitals &vitals);
}
