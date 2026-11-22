#pragma once

#include "game/content/RulesetOptions.h"
#include "game/party/Party.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// A co-op player's character in a file of its own (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The
// character file"): it is carried into any host's world, and what it gained there is written back. It belongs to no
// world: its quests and journal are each world's own and are not in it.
struct CharacterFile
{
    // Names the character for good, whatever its file is called.
    std::array<uint8_t, 16> id = {};
    // Counts the times the file was written: of two copies the higher is the later.
    uint32_t revision = 0;
    // The ruleset the character was made under; it joins worlds of that ruleset.
    RulesetSelection ruleset;
    // The character, with what the ruleset keeps for it (Party::Snapshot::rulesetState) and without a campaign.
    Party::Snapshot character;

    // The character's name, class and level, for lists.
    std::string describe() const;
};

// Where the character files are kept: saves/characters, beside the saves.
std::filesystem::path characterFileFolder();
// The file of a character by the name a player gives it (letters, digits, '-' and '_' are kept, the rest becomes
// '_'); nothing for a name that leaves nothing.
std::optional<std::filesystem::path> characterFilePath(const std::string &name);

// A new character file of a party: a copy that lives on by itself, with an id of its own. Only the first member
// goes along, as a co-op character is one character.
CharacterFile makeCharacterFile(const Party::Snapshot &party, const RulesetSelection &ruleset);

// Writes the file in place of the one there: into a temporary file first, the file there is kept as `.bak`, then the
// new one takes its name. The revision in `file` is counted up.
bool writeCharacterFile(const std::filesystem::path &path, CharacterFile &file, std::string &error);
// Reads a file written by this or an older build (the character is read as a save's party is).
std::optional<CharacterFile> readCharacterFile(const std::filesystem::path &path, std::string &error);
// The character files in the folder, by file name.
std::vector<std::filesystem::path> listCharacterFiles();
}
