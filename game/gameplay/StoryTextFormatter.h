#pragma once

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class Party;

class StoryTextFormatter
{
public:
    static std::string format(const std::string &text, const Party &party, int32_t unlockedGameMinutes);
};
}
