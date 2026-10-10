#include "game/maps/StaleLightingNote.h"

#include <doctest/doctest.h>

#include <filesystem>
#include <fstream>
#include <sstream>

using namespace OpenYAMM;

namespace
{
std::string readNote(const std::filesystem::path &path)
{
    std::ifstream in(path);
    std::ostringstream text;
    text << in.rdbuf();
    return text.str();
}
}

TEST_CASE("stale lighting bakes are noted and cleared per map")
{
    const std::filesystem::path directory =
        std::filesystem::temp_directory_path() / "openyamm_stale_lighting_note_test";
    std::filesystem::remove_all(directory);
    std::filesystem::create_directories(directory);
    const std::filesystem::path note = directory / Game::StaleLightingNoteFileName;

    // A fresh bake leaves no note behind.
    CHECK(Game::updateStaleLightingNote(note, "worlds/mm6/maps/oute3.lighting", {}));
    CHECK_FALSE(std::filesystem::exists(note));

    CHECK(Game::updateStaleLightingNote(note, "worlds/mm6/maps/oute3.lighting",
        {"worlds/mm6/models/mm6_deco_cauldron.glb", "worlds/mm6/models/mm6_deco_campfire.glb"}));
    CHECK(Game::updateStaleLightingNote(note, "worlds/mm6/maps/outb1.lighting",
        {"worlds/mm6/models/mm6_deco_burningrock.glb"}));
    const std::string both = readNote(note);
    CHECK(both.find("worlds/mm6/maps/oute3.lighting: worlds/mm6/models/mm6_deco_cauldron.glb, "
        "worlds/mm6/models/mm6_deco_campfire.glb\n") != std::string::npos);
    CHECK(both.find("worlds/mm6/maps/outb1.lighting: worlds/mm6/models/mm6_deco_burningrock.glb\n")
        != std::string::npos);
    // Sorted by bake, below the header.
    CHECK(both.find("outb1.lighting") < both.find("oute3.lighting"));

    // Re-baked maps clear their own line; the last one removes the note.
    CHECK(Game::updateStaleLightingNote(note, "worlds/mm6/maps/oute3.lighting", {}));
    CHECK(readNote(note).find("oute3.lighting") == std::string::npos);
    CHECK(readNote(note).find("outb1.lighting") != std::string::npos);
    CHECK(Game::updateStaleLightingNote(note, "worlds/mm6/maps/outb1.lighting", {}));
    CHECK_FALSE(std::filesystem::exists(note));
    std::filesystem::remove_all(directory);
}
