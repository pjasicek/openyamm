#include "game/gameplay/CombatLog.h"

#include "game/rules/DamagePipeline.h"

#include <cstddef>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
CombatLog *g_pBoundCombatLog = nullptr;
}

bool CombatLog::recording() const
{
    return m_recording;
}

void CombatLog::setRecording(bool recording)
{
    if (m_recording && !recording)
    {
        m_pendingStages.clear();
    }

    m_recording = recording;
}

void CombatLog::recordStages(bool onCharacter, int finalAmount, const std::vector<DamageStageRecord> &records)
{
    if (!m_recording)
    {
        return;
    }

    PendingStages pending;
    pending.onCharacter = onCharacter;
    pending.finalAmount = finalAmount;
    pending.stages.reserve(records.size());

    for (const DamageStageRecord &record : records)
    {
        pending.stages.push_back({record.stage, record.before, record.after});
    }

    m_pendingStages.push_back(std::move(pending));

    while (m_pendingStages.size() > MaxPendingStages)
    {
        m_pendingStages.pop_front();
    }
}

void CombatLog::add(CombatLogEntry entry, bool takeStages)
{
    if (!m_recording)
    {
        return;
    }

    entry.id = m_nextId++;
    entry.gameMinutes = m_gameMinutes;
    entry.stages.clear();
    const int amount = entry.amount;
    const bool onCharacter = entry.kind == CombatLogKind::Taken;

    for (size_t index = 0; takeStages && index < m_pendingStages.size(); ++index)
    {
        const PendingStages &pending = m_pendingStages[index];

        if (pending.onCharacter != onCharacter || pending.finalAmount != amount)
        {
            continue;
        }

        entry.stages = std::move(m_pendingStages[index].stages);

        // Hits of the same kind before it were never worded (misses, hidden targets): drop them with it.
        for (size_t dropped = index + 1; dropped-- > 0;)
        {
            if (m_pendingStages[dropped].onCharacter == onCharacter)
            {
                m_pendingStages.erase(m_pendingStages.begin() + std::ptrdiff_t(dropped));
            }
        }

        break;
    }

    m_entries.push_back(std::move(entry));

    while (m_entries.size() > MaxEntries)
    {
        m_entries.pop_front();
    }

    ++m_revision;
}

void CombatLog::setGameMinutes(float gameMinutes)
{
    m_gameMinutes = gameMinutes;
}

void CombatLog::clear()
{
    m_entries.clear();
    m_pendingStages.clear();
    ++m_revision;
}

const std::deque<CombatLogEntry> &CombatLog::entries() const
{
    return m_entries;
}

uint64_t CombatLog::revision() const
{
    return m_revision;
}

CombatLog *boundCombatLog()
{
    return g_pBoundCombatLog;
}

void bindCombatLog(CombatLog *pLog)
{
    g_pBoundCombatLog = pLog;
}
}
