#include "game/mm9/Mm9JournalContent.h"

#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/party/Party.h"

#include <cstdlib>
#include <map>
#include <optional>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::optional<int32_t> parseInt(const std::string &text)
{
    if (text.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const long value = std::strtol(text.c_str(), &pEnd, 10);
    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(value);
}

uint32_t stateQbitIdForRawId(const Mm9DialoguePackage &package, int32_t rawId)
{
    const std::map<int32_t, Mm9GeneratedKey>::const_iterator keyIterator = package.keys.find(rawId);
    if (keyIterator != package.keys.end() && keyIterator->second.qbitId > 0)
    {
        return static_cast<uint32_t>(keyIterator->second.qbitId);
    }

    return mm9KeyQbitIdForRawKey(rawId);
}

std::vector<Mm9JournalStateRef> collectStateRefs(
    const Mm9DialoguePackage &package,
    const Mm9GeneratedRudeRow &row)
{
    std::vector<Mm9JournalStateRef> refs;
    for (size_t columnIndex = 6; columnIndex < row.rawColumns.size(); ++columnIndex)
    {
        const std::optional<int32_t> rawId = parseInt(row.rawColumns[columnIndex]);
        if (!rawId || *rawId <= 0)
        {
            continue;
        }

        Mm9JournalStateRef ref = {};
        ref.column = columnIndex + 1;
        ref.rawId = *rawId;
        ref.qbitId = stateQbitIdForRawId(package, *rawId);
        refs.push_back(ref);
    }
    return refs;
}

bool allStateRefsVisible(const std::vector<Mm9JournalStateRef> &refs, const Party &party)
{
    if (refs.empty())
    {
        return true;
    }

    for (const Mm9JournalStateRef &ref : refs)
    {
        if (ref.qbitId == 0 || !party.hasQuestBit(ref.qbitId))
        {
            return false;
        }
    }
    return true;
}

std::vector<Mm9JournalRenderEntry> buildJournalEntries(
    const Mm9DialoguePackage &package,
    const std::vector<Mm9GeneratedRudeRow> &rows,
    const Party &party)
{
    std::vector<Mm9JournalRenderEntry> entries;
    entries.reserve(rows.size());

    for (const Mm9GeneratedRudeRow &row : rows)
    {
        Mm9JournalRenderEntry entry = {};
        entry.source = row.source;
        entry.entryId = row.choiceSlot;
        entry.title = row.prompt;
        entry.text = row.response == "blank" ? std::string() : row.response;
        entry.stateRefs = collectStateRefs(package, row);
        entry.visible = allStateRefsVisible(entry.stateRefs, party);
        entries.push_back(std::move(entry));
    }

    return entries;
}
}

std::vector<Mm9JournalRenderEntry> buildMm9QuestRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party)
{
    return buildJournalEntries(package, package.journalQuestRows, party);
}

std::vector<Mm9JournalRenderEntry> buildMm9NoteRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party)
{
    return buildJournalEntries(package, package.journalNoteRows, party);
}

std::vector<Mm9AwardRenderEntry> buildMm9AwardRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party,
    size_t memberIndex)
{
    std::vector<Mm9AwardRenderEntry> entries;
    entries.reserve(package.awardRows.size());

    for (const Mm9GeneratedRudeRow &row : package.awardRows)
    {
        if (row.rawColumns.size() < 7)
        {
            continue;
        }

        const std::optional<int32_t> awardId = parseInt(row.rawColumns[6]);
        if (!awardId || *awardId <= 0)
        {
            continue;
        }

        Mm9AwardRenderEntry entry = {};
        entry.source = row.source;
        entry.awardId = static_cast<uint32_t>(*awardId);
        entry.text = row.prompt;
        entry.visible = party.hasAward(memberIndex, entry.awardId);
        entries.push_back(std::move(entry));
    }

    return entries;
}
}
