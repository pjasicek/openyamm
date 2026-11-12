#include "doctest/doctest.h"

#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/maps/SaveGame.h"

#include <algorithm>
#include <filesystem>
#include <optional>
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

TEST_CASE("a new quicksave pushes the playthrough's earlier quicksaves down a slot")
{
    CHECK(quickSaveSlot("saves/quicksave.oysav") == 1);
    CHECK(quickSaveSlot("saves/quicksave_abc.oysav") == 1);
    CHECK(quickSaveSlot("saves/quicksave_2.oysav") == 1);
    CHECK(quickSaveSlot("saves/quicksave2.oysav") == 2);
    CHECK(quickSaveSlot("saves/quicksave2_abc.oysav") == 2);
    CHECK(quickSaveSlot("saves/Quicksave20_abc.oysav") == 20);
    CHECK(quickSaveSlot(quickSavePath("abc", MaxQuickSaveSlotCount)) == MaxQuickSaveSlotCount);
    CHECK(quickSaveSlot("saves/quicksave21_abc.oysav") == 0);
    CHECK(quickSaveSlot("saves/quicksave1_abc.oysav") == 0);
    CHECK(quickSaveSlot("saves/quicksave02_abc.oysav") == 0);
    CHECK(quickSaveSlot("saves/quicksave200.oysav") == 0);
    CHECK(quickSaveSlot("saves/quicksaves.oysav") == 0);
    CHECK(quickSaveSlot("saves/quicksave2b.oysav") == 0);
    CHECK(quickSaveSlot("saves/autosave_abc.oysav") == 0);
    CHECK(quickSaveSlot("saves/save2.oysav") == 0);
    CHECK(isQuickSavePath("saves/quicksave3.oysav"));
    CHECK_FALSE(isAutosavePath("saves/quicksave3.oysav"));

    const std::filesystem::path directory = std::filesystem::temp_directory_path() / "openyamm_quicksave_rotation_test";
    std::filesystem::remove_all(directory);
    const auto slotPath = [&directory](int slot)
    {
        return directory / quickSavePath("abc", slot).filename();
    };
    const auto write = [&slotPath](const std::string &name, int slotCount)
    {
        GameSaveData data = {};
        data.saveName = name;
        std::string error;
        return saveQuickSaveToPath(slotPath(1), data, slotCount, error);
    };
    const auto nameIn = [&slotPath](int slot)
    {
        std::string error;
        const std::optional<GameSaveSummary> summary = loadGameSaveSummaryFromPath(slotPath(slot), error);
        return summary ? summary->saveName : std::string("<none>");
    };
    const auto fileCount = [&directory]()
    {
        size_t count = 0;

        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(directory))
        {
            CHECK(entry.path().extension() == ".oysav");
            ++count;
        }

        return count;
    };

    REQUIRE(write("first", 3));
    CHECK(nameIn(1) == "first");
    CHECK(nameIn(2) == "<none>");

    REQUIRE(write("second", 3));
    REQUIRE(write("third", 3));
    CHECK(nameIn(1) == "third");
    CHECK(nameIn(2) == "second");
    CHECK(nameIn(3) == "first");

    // All slots taken: the oldest goes.
    REQUIRE(write("fourth", 3));
    CHECK(nameIn(1) == "fourth");
    CHECK(nameIn(2) == "third");
    CHECK(nameIn(3) == "second");

    // A deleted quicksave leaves a free slot, which takes the shift: the oldest stays.
    std::filesystem::remove(slotPath(2));
    REQUIRE(write("fifth", 3));
    CHECK(nameIn(1) == "fifth");
    CHECK(nameIn(2) == "fourth");
    CHECK(nameIn(3) == "second");
    CHECK(fileCount() == 3);

    // A larger setting keeps more.
    REQUIRE(write("sixth", 5));
    REQUIRE(write("seventh", 5));
    REQUIRE(write("eighth", 5));
    CHECK(nameIn(1) == "eighth");
    CHECK(nameIn(4) == "fifth");
    CHECK(nameIn(5) == "fourth");
    CHECK(fileCount() == 5);

    // A lowered setting drops the slots past it at the next quicksave.
    REQUIRE(write("ninth", 2));
    CHECK(nameIn(1) == "ninth");
    CHECK(nameIn(2) == "eighth");
    CHECK(fileCount() == 2);

    // One slot: the quicksave replaces itself, as before the rotation.
    REQUIRE(write("tenth", 1));
    CHECK(nameIn(1) == "tenth");
    CHECK(fileCount() == 1);

    // Another playthrough's quicksaves are not touched.
    {
        GameSaveData data = {};
        data.saveName = "other";
        std::string error;
        REQUIRE(saveQuickSaveToPath(directory / quickSavePath("abcd").filename(), data, 1, error));
    }

    REQUIRE(write("eleventh", 1));
    CHECK(fileCount() == 2);
    std::filesystem::remove_all(directory);
}
