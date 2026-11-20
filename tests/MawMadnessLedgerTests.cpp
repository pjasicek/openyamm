#include "doctest/doctest.h"
#include "game/rules/maw/MawMadnessLedger.h"

#include <chrono>
#include <filesystem>

using namespace OpenYAMM::Game;

TEST_CASE("Beyond Madness's ledger counts deaths and reloads during a fight (P9.M8)")
{
    const std::filesystem::path folder = std::filesystem::temp_directory_path()
        / ("openyamm_madness_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    const std::filesystem::path file = folder / "deaths.txt";

    {
        MawMadnessLedger ledger(file);
        ledger.startRun(42);
        CHECK_EQ(ledger.deaths(), 0);

        // A hit marks the run; five quiet minutes with enemies near clear it, a death counts one.
        ledger.markHit(100);
        CHECK(ledger.pending());
        ledger.update(104, true);
        CHECK(ledger.pending());
        ledger.update(105, true);
        CHECK_FALSE(ledger.pending());
        ledger.markHit(200);
        ledger.partyDied();
        CHECK_EQ(ledger.deaths(), 1);
        CHECK_FALSE(ledger.pending());

        // With no enemy near the wait drops to its last half minute, counted from the first quiet frame.
        ledger.markHit(300);
        ledger.update(300.4, false);
        CHECK(ledger.pending());
        ledger.update(300.85, false);
        CHECK(ledger.pending());
        ledger.update(300.9, false);
        CHECK_FALSE(ledger.pending());

        // Hit, then the player quits or loads: the mark stays in the file.
        ledger.markHit(400);
    }

    // Another run in the same file is kept apart.
    MawMadnessLedger other(file);
    other.startRun(7);
    other.partyDied();

    MawMadnessLedger reloaded(file);
    CHECK(reloaded.loadRun(42));
    CHECK_EQ(reloaded.deaths(), 2);
    CHECK_FALSE(reloaded.pending());
    // Loading again counts nothing more; leaving a map clears a mark.
    CHECK_FALSE(reloaded.loadRun(42));
    reloaded.markHit(10);
    reloaded.leaveMap();
    CHECK_FALSE(reloaded.loadRun(42));
    CHECK_EQ(reloaded.deaths(), 2);
    MawMadnessLedger seven(file);
    CHECK_FALSE(seven.loadRun(7));
    CHECK_EQ(seven.deaths(), 1);

    // A run the file has no line for (a save from another installation) starts from the save's count; a line in the
    // file wins over it.
    MawMadnessLedger moved(file);
    CHECK_FALSE(moved.loadRun(99, 3));
    CHECK_EQ(moved.deaths(), 3);
    MawMadnessLedger known(file);
    known.loadRun(7, 5);
    CHECK_EQ(known.deaths(), 1);

    std::filesystem::remove_all(folder);
}
