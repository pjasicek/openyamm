#pragma once

#include "game/rules/MonsterInspect.h"

#include <string>

namespace OpenYAMM::Game
{
class MawRules;

// MAW's monster inspect panel (BuildMonsterInformationBox, zzMaw-Monsters.lua:1964-2131): the level; for each attack
// and the spell the range 95 % of hits fall in (the attack's model damage with its ±25 % spread, a dimension map's
// damage affix included), after the viewer's armour and resistances unless the raw numbers are asked for; the special
// attack, the experience a kill gives the viewer and the Grandmaster spear's and legendary 29's stacks, with timers on
// the monster's effects.
MonsterInspectNumbers mawMonsterInspectNumbers(const MawRules &rules, const MonsterInspectQuery &query);

// A number as MAW's panels shorten it (shortenNumber, zz_Maw-initialize.lua:362-433): whole below 1000, else `digits`
// significant digits with K, M or B, coloured yellow, orange or red unless `coloured` is false.
std::string mawShortNumber(double number, bool coloured = true, int digits = 3);
}
