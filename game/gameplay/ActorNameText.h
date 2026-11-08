#pragma once

#include <string>

namespace OpenYAMM::Game
{
// A monster's name as the player reads it. Actors keep English names (statistics, saves, lookups); a ruleset may
// compose them ("Resurrected Venomous Goblin", MAW), and the parts are translated through templates.
std::string localizedActorName(const std::string &englishName);
}
