#include "game/ActorNameResolver.h"

namespace OpenYAMM::Game
{
std::string resolveMapDeltaActorName(const MonsterTable &monsterTable, const MapDeltaActor &actor)
{
    if (actor.uniqueNameIndex > 0)
    {
        const std::optional<std::string> uniqueName = monsterTable.getUniqueName(actor.uniqueNameIndex);

        if (uniqueName && !uniqueName->empty())
        {
            return *uniqueName;
        }
    }

    const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        monsterTable.findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr && !pDisplayEntry->displayName.empty())
    {
        return pDisplayEntry->displayName;
    }

    if (!actor.name.empty())
    {
        return actor.name;
    }

    const MonsterEntry *pMonsterEntry = monsterTable.findById(actor.monsterId);

    if (pMonsterEntry == nullptr)
    {
        return {};
    }

    const std::optional<std::string> displayName =
        monsterTable.findDisplayNameByInternalName(pMonsterEntry->internalName);
    return displayName ? *displayName : pMonsterEntry->internalName;
}
}
