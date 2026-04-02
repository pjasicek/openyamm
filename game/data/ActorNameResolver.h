#pragma once

#include "game/maps/MapDeltaData.h"
#include "game/tables/MonsterTable.h"

#include <string>

namespace OpenYAMM::Game
{
std::string resolveMapDeltaActorName(const MonsterTable &monsterTable, const MapDeltaActor &actor);
}
