#pragma once

#include <cstdint>
#include <filesystem>
#include <optional>

namespace OpenYAMM::Game
{
// Beyond Madness's death count (zzMaw-Monsters.lua:2289-2534, Damage.lua:1567-1573), kept outside the save so loading
// cannot undo a death (devdocs/maw/PHASE9_SCOPE.md P9.M8, Q4). A monster's hit marks the run pending; it clears five
// game minutes after the last hit (about 30 game seconds once no enemy is near), on leaving the map and on the party's
// death, which counts one. A run still pending when a save is loaded counts a death: the player reloaded mid-fight.
// The ledger is a plain text file, one line per run: "<run id> <deaths> <pending 0|1>".
class MawMadnessLedger
{
public:
    explicit MawMadnessLedger(std::filesystem::path file);

    // A new game's run (its random root seed), with no deaths.
    void startRun(uint64_t runId);
    // A loaded game's run: a pending mark left in the ledger counts a death. Returns whether one was counted. A run the
    // ledger has no line for (a save from another installation) starts from the save's count.
    bool loadRun(uint64_t runId, int savedDeaths = 0);
    // A monster hit the party at this game time.
    void markHit(double gameMinutes);
    // Each frame: clears the pending mark once the wait is over.
    void update(double gameMinutes, bool enemiesNear);
    void leaveMap();
    void partyDied();

    int deaths() const;
    bool pending() const;
    // Game minutes until the pending mark clears, or nothing while not pending.
    std::optional<double> pendingMinutesLeft(double gameMinutes) const;

private:
    struct Entry
    {
        int deaths = 0;
        bool pending = false;
    };

    std::optional<Entry> read(uint64_t runId) const;
    void write(uint64_t runId, const Entry &entry) const;

    std::filesystem::path m_file;
    std::optional<uint64_t> m_runId;
    Entry m_entry;
    double m_lastHitMinutes = 0;
};
}
