#pragma once

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class JournalQuestTable;
class Party;

std::vector<std::string> buildCurrentQuestTexts(const JournalQuestTable &questTable, const Party &party);
} // namespace OpenYAMM::Game
