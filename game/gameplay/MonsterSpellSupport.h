#pragma once

#include <string>

namespace OpenYAMM::Game
{
bool isMonsterProjectileSpellName(const std::string &spellName);
bool isMonsterSelfBuffSpellName(const std::string &spellName);
bool isMonsterSelfActionSpellName(const std::string &spellName);
}
