#pragma once

#include "game/mm9/Mm9DialoguePackage.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;

struct Mm9JournalStateRef
{
    size_t column = 0;
    int32_t rawId = 0;
    uint32_t qbitId = 0;
};

struct Mm9JournalRenderEntry
{
    Mm9GeneratedRudeSource source;
    int32_t entryId = 0;
    std::string title;
    std::string text;
    std::vector<Mm9JournalStateRef> stateRefs;
    bool visible = false;
};

struct Mm9AwardRenderEntry
{
    Mm9GeneratedRudeSource source;
    uint32_t awardId = 0;
    std::string text;
    bool visible = false;
};

std::vector<Mm9JournalRenderEntry> buildMm9QuestRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party);

std::vector<Mm9JournalRenderEntry> buildMm9NoteRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party);

std::vector<Mm9AwardRenderEntry> buildMm9AwardRenderEntries(
    const Mm9DialoguePackage &package,
    const Party &party,
    size_t memberIndex);
}
