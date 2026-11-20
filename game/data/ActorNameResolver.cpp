#include "game/data/ActorNameResolver.h"

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

    // An MM9 person with its own RUDE dialogue is called by its name (the one its dialogue shows: Ludwig Van, Brother
    // Kennet), not by its body's row (Commoner, Shopkeeper, Monk).
    if (actor.mm9RudeId > 0 && !actor.name.empty())
    {
        return actor.name;
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
