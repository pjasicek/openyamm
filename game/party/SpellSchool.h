#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
std::optional<std::string> resolveMagicSkillName(uint32_t spellId);
std::optional<std::pair<uint32_t, uint32_t>> spellIdRangeForMagicSkill(const std::string &skillName);
}
