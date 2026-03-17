#pragma once

#include "game/MapDeltaData.h"
#include "game/MonsterTable.h"

#include <string>

namespace OpenYAMM::Game
{
std::string resolveMapDeltaActorName(const MonsterTable &monsterTable, const MapDeltaActor &actor);
}
