#include "game/rules/maw/MawMadnessLedger.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <string>
#include <system_error>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// MAW's waits: five game minutes after a hit, cut to the last half minute once no enemy is near.
constexpr double PendingMinutes = 5;
constexpr double ClearPendingMinutes = 0.5;
}

MawMadnessLedger::MawMadnessLedger(std::filesystem::path file)
    : m_file(std::move(file))
{
}

void MawMadnessLedger::startRun(uint64_t runId)
{
    m_runId = runId;
    m_entry = {};
    m_lastHitMinutes = 0;
    write(runId, m_entry);
}

bool MawMadnessLedger::loadRun(uint64_t runId, int savedDeaths)
{
    m_runId = runId;
    const std::optional<Entry> entry = read(runId);
    m_entry = entry.value_or(Entry{std::max(savedDeaths, 0), false});
    m_lastHitMinutes = 0;
    const bool counted = m_entry.pending;


    if (counted)
    {
        ++m_entry.deaths;
        m_entry.pending = false;
        write(runId, m_entry);
    }

    return counted;
}

void MawMadnessLedger::markHit(double gameMinutes)
{
    if (!m_runId)
    {
        return;
    }

    m_lastHitMinutes = gameMinutes;

    if (!m_entry.pending)
    {
        m_entry.pending = true;
        write(*m_runId, m_entry);
    }
}

void MawMadnessLedger::update(double gameMinutes, bool enemiesNear)
{
    if (!m_runId || !m_entry.pending)
    {
        return;
    }

    if (!enemiesNear)
    {
        m_lastHitMinutes = std::min(m_lastHitMinutes, gameMinutes - (PendingMinutes - ClearPendingMinutes));
    }

    if (gameMinutes >= m_lastHitMinutes + PendingMinutes)
    {
        m_entry.pending = false;
        write(*m_runId, m_entry);
    }
}

void MawMadnessLedger::leaveMap()
{
    if (m_runId && m_entry.pending)
    {
        m_entry.pending = false;
        write(*m_runId, m_entry);
    }
}

void MawMadnessLedger::partyDied()
{
    if (!m_runId)
    {
        return;
    }

    ++m_entry.deaths;
    m_entry.pending = false;
    write(*m_runId, m_entry);
}

int MawMadnessLedger::deaths() const
{
    return m_entry.deaths;
}

bool MawMadnessLedger::pending() const
{
    return m_entry.pending;
}

std::optional<double> MawMadnessLedger::pendingMinutesLeft(double gameMinutes) const
{
    if (!m_entry.pending)
    {
        return std::nullopt;
    }

    return std::max(0.0, m_lastHitMinutes + PendingMinutes - gameMinutes);
}

std::optional<MawMadnessLedger::Entry> MawMadnessLedger::read(uint64_t runId) const
{
    std::ifstream input(m_file);
    std::string line;

    while (std::getline(input, line))
    {
        std::istringstream fields(line);
        uint64_t id = 0;
        Entry entry;
        int pending = 0;

        if (fields >> id >> entry.deaths >> pending && id == runId)
        {
            entry.pending = pending != 0;
            return entry;
        }
    }

    return std::nullopt;
}

void MawMadnessLedger::write(uint64_t runId, const Entry &entry) const
{
    // Every other run's line is kept as it is; the file is replaced in one rename.
    std::ifstream input(m_file);
    std::ostringstream contents;
    std::string line;

    while (std::getline(input, line))
    {
        std::istringstream fields(line);
        uint64_t id = 0;

        if (!(fields >> id) || id != runId)
        {
            contents << line << '\n';
        }
    }

    input.close();
    contents << runId << ' ' << entry.deaths << ' ' << (entry.pending ? 1 : 0) << '\n';
    std::error_code error;

    if (!m_file.parent_path().empty())
    {
        std::filesystem::create_directories(m_file.parent_path(), error);
    }

    const std::filesystem::path temporary = m_file.string() + ".tmp";
    {
        std::ofstream output(temporary, std::ios::trunc);
        output << contents.str();
    }
    std::filesystem::rename(temporary, m_file, error);
}
}
