#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
class JournalQuestTable;
class Party;

std::vector<std::string> buildCurrentQuestTexts(const JournalQuestTable &questTable, const Party &party,
    std::string_view owner = {});
} // namespace OpenYAMM::Game
