#include "game/data/ActorNameResolver.h"

#include "game/tables/NpcDialogTable.h"

#include <utility>

namespace OpenYAMM::Game
{
std::optional<std::string> resolveActorNpcName(int32_t npcId, const ActorNpcNameTables &npcNames)
{
    if (npcId <= 0 || npcNames.pNpcDialogTable == nullptr)
    {
        return std::nullopt;
    }

    const NpcEntry *pNpc = npcNames.pNpcDialogTable->getNpc(uint32_t(npcId));

    if (pNpc == nullptr || pNpc->name.empty())
    {
        return std::nullopt;
    }

    return npcNameAndTitle(*pNpc, npcNames.pNpcProfessionTable);
}

std::string resolveMapDeltaActorName(
    const MonsterTable &monsterTable,
    const MapDeltaActor &actor,
    const ActorNpcNameTables &npcNames)
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

    // An actor with an NPC id is that NPC (MM6-MM8, a placed talking figure on a peasant row), not its body's row.
    if (std::optional<std::string> npcName = resolveActorNpcName(actor.npcId, npcNames))
    {
        return std::move(*npcName);
    }

    if (!actor.actorProfile.empty())
    {
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(
            actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId, actor.actorProfile);
        if (pStats != nullptr)
        {
            return pStats->name;
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
