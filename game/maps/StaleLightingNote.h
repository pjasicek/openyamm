#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Outdoor lighting bakes older than a file they were baked from are loaded as they are during development and noted
// in <asset root>/STALE_LIGHTING_BAKES.txt (one line per bake: its path and the changed sources). Loading a map with a
// fresh bake clears its line, and the file goes away when empty. tools/lighting/stale_bakes.py rechecks every bake
// and rewrites the note; run it before a release or a commit.
inline constexpr const char *StaleLightingNoteFileName = "STALE_LIGHTING_BAKES.txt";

// Records (staleSources non-empty) or clears the note line of one bake (a virtual asset path). Rewrites the note only
// when the line changes; false when it cannot be written.
bool updateStaleLightingNote(const std::filesystem::path &noteFile, const std::string &lightingPath,
    const std::vector<std::string> &staleSources);
}
