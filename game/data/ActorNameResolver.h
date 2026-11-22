#pragma once

#include "game/maps/MapDeltaData.h"
#include "game/tables/MonsterTable.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class MergedNpcProfessionTable;
class NpcDialogTable;

// The tables an actor with an NPC id is named from (npcNameAndTitle). Without them the actor keeps its row's name.
struct ActorNpcNameTables
{
    const NpcDialogTable *pNpcDialogTable = nullptr;
    const MergedNpcProfessionTable *pNpcProfessionTable = nullptr;
};

// The name an actor with this NPC id goes by, as its talk's title names it ("Derek, Ranger"); nothing without an NPC
// id, the tables or a named NPC row.
std::optional<std::string> resolveActorNpcName(int32_t npcId, const ActorNpcNameTables &npcNames);

// An actor's displayed name: its unique name, an MM9 RUDE person's own name, its NPC as its talk's title names it
// ("Derek, Ranger"; OpenEnroth's Actor::GetDisplayName), then its monster row's name.
std::string resolveMapDeltaActorName(
    const MonsterTable &monsterTable,
    const MapDeltaActor &actor,
    const ActorNpcNameTables &npcNames);
}
