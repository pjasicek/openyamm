#include "doctest/doctest.h"

#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/maps/SaveGame.h"

#include <algorithm>
#include <filesystem>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("save location labels resolve legacy and canonical map ids")
{
    MapStatsEntry sorpigal = {};
    sorpigal.fileName = "oute3.odm";
    sorpigal.canonicalId = "mm6:oute3.odm";
    sorpigal.name = "New Sorpigal";
    MapStatsEntry goblinwatch = {};
    goblinwatch.fileName = "6d01.blv";
    goblinwatch.canonicalId = "mm6:6d01.blv";
    goblinwatch.name = "Goblinwatch";
    const std::vector<MapStatsEntry> maps = {sorpigal, goblinwatch};

    CHECK(resolveSaveLocationName(maps, "OUTE3.ODM") == "New Sorpigal");
    CHECK(resolveSaveLocationName(maps, "MM6:OUTE3.ODM") == "New Sorpigal");
    CHECK(resolveSaveLocationName(maps, "6d01.blv") == "Goblinwatch");
    CHECK(resolveSaveLocationName(maps, "mm6:6d01.blv") == "Goblinwatch");
    CHECK(resolveSaveLocationName(maps, "custom.blv") == "custom.blv");
    CHECK(resolveSaveLocationName(maps, "").empty());
}

TEST_CASE("save game name conflict ignores target slot and empty slots")
{
    GameplayUiController::SaveGameScreenState screen = {};
    GameplayUiController::SaveSlotSummary firstSlot = {};
    firstSlot.fileLabel = "Castle Alamos";
    firstSlot.populated = true;
    screen.slots.push_back(firstSlot);

    GameplayUiController::SaveSlotSummary secondSlot = {};
    secondSlot.fileLabel = "Empty";
    secondSlot.populated = false;
    screen.slots.push_back(secondSlot);

    CHECK_FALSE(saveGameNameConflictsWithExistingSlot(screen, "Castle Alamos", 0));
    CHECK(saveGameNameConflictsWithExistingSlot(screen, "castle alamos", 1));
    CHECK_FALSE(saveGameNameConflictsWithExistingSlot(screen, "Empty", 1));
    CHECK_FALSE(saveGameNameConflictsWithExistingSlot(screen, "   ", 1));
}

TEST_CASE("save lists sort by shown name with numbers in order, after Quicksave and Autosave")
{
    struct Entry
    {
        std::filesystem::path path;
        std::string name;
    };

    std::vector<Entry> entries = {
        {"saves/save1.oysav", "Free Haven Sewer 1"},
        {"saves/save10.oysav", "Free Haven 2"},
        {"saves/save11.oysav", "Free Haven Sewer 2"},
        {"saves/save2.oysav", "free haven sewer 10"},
        {"saves/autosave.oysav", "Autosave"},
        {"saves/save3.oysav", "Bootleg Bay 2"},
        {"saves/quicksave.oysav", "Quicksave"},
        {"saves/save4.oysav", "Free Haven 1"},
    };
    std::sort(entries.begin(), entries.end(), [](const Entry &left, const Entry &right)
        {
            return compareSavesForDisplay(left.path, left.name, right.path, right.name);
        });
    std::vector<std::string> names;

    for (const Entry &entry : entries)
    {
        names.push_back(entry.name);
    }

    const std::vector<std::string> expected = {
        "Quicksave",
        "Autosave",
        "Bootleg Bay 2",
        "Free Haven 1",
        "Free Haven 2",
        "Free Haven Sewer 1",
        "Free Haven Sewer 2",
        "free haven sewer 10",
    };
    CHECK(names == expected);
    CHECK(compareSaveNamesNaturally("Sewer 02", "Sewer 2") == 0);
    CHECK(compareSaveNamesNaturally("Sewer", "Sewer 1") < 0);
}
