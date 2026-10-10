#include "game/maps/StaleLightingNote.h"

#include <fstream>
#include <map>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *NoteHeader =
    "# Outdoor lighting bakes older than a file they were baked from (noted by the game and by\n"
    "# tools/lighting/stale_bakes.py). Re-bake each map, then run tools/lighting/stale_bakes.py.\n";
}

bool updateStaleLightingNote(const std::filesystem::path &noteFile, const std::string &lightingPath,
    const std::vector<std::string> &staleSources)
{
    std::map<std::string, std::string> entries;
    if (std::ifstream in(noteFile); in)
    {
        std::string line;
        while (std::getline(in, line))
        {
            const size_t separator = line.find(": ");
            if (!line.empty() && line.front() != '#' && separator != std::string::npos)
            {
                entries[line.substr(0, separator)] = line.substr(separator + 2);
            }
        }
    }
    std::string sources;
    for (const std::string &source : staleSources)
    {
        sources += (sources.empty() ? "" : ", ") + source;
    }
    const auto found = entries.find(lightingPath);
    if (sources.empty() ? found == entries.end() : found != entries.end() && found->second == sources)
    {
        return true;
    }
    if (sources.empty())
    {
        entries.erase(found);
    }
    else
    {
        entries[lightingPath] = sources;
    }
    std::error_code error;
    if (entries.empty())
    {
        std::filesystem::remove(noteFile, error);
        return !error;
    }
    std::ostringstream text;
    text << NoteHeader;
    for (const auto &[path, changed] : entries)
    {
        text << path << ": " << changed << '\n';
    }
    // Written beside and renamed over the note, so another game instance never reads half a note.
    const std::filesystem::path temporary = noteFile.string() + ".tmp";
    {
        std::ofstream out(temporary, std::ios::trunc);
        out << text.str();
        if (!out)
        {
            return false;
        }
    }
    std::filesystem::rename(temporary, noteFile, error);
    return !error;
}
}
