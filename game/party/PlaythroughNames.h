#pragma once

#include <filesystem>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
// The names players give their playthroughs in the save lists: `names.yml` in the playthrough statistics folder, a
// map of playthrough id to name. It is apart from the statistics files, which are sealed and exist only for
// playthroughs played here; a playthrough without a name of its own is shown by its start continent and rules.
std::unordered_map<std::string, std::string> readPlaythroughNames(const std::filesystem::path &directory);
// Sets a playthrough's name; an empty name removes it. False when the file cannot be written.
bool writePlaythroughName(
    const std::filesystem::path &directory,
    const std::string &playthroughId,
    const std::string &name);
}
