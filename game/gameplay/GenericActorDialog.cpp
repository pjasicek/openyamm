#include "game/gameplay/GenericActorDialog.h"

#include "game/tables/NpcDialogTable.h"

namespace OpenYAMM::Game
{
namespace
{
uint32_t resolveGenericNpcId(const std::string &actorName, uint32_t actorGroup)
{
    if (actorName == "Lizardman Peasant")
    {
        return 516;
    }

    if (actorName == "Lizardman Villager")
    {
        return 516;
    }

    if (actorName == "Lizardman Guard"
        || actorName == "Guard"
        || actorName == "Lizardman Soldier"
        || actorName == "Lizardman Warrior"
        || actorName == "Lizardman Lookout")
    {
        return 517;
    }

    if (actorName == "Dark Elf Peasant")
    {
        return 518;
    }

    if (actorName == "Dark Elf Guard")
    {
        return 519;
    }

    if (actorName == "Ogre Peasant")
    {
        return 520;
    }

    if (actorName == "Wererat Peasant" || actorName == "Wererat Peasants")
    {
        return 521;
    }

    if (actorName == "Troll Peasant")
    {
        return 522;
    }

    if (actorName == "Dragon Hunter")
    {
        return 523;
    }

    if (actorName == "Necromancer Peasant")
    {
        return 524;
    }

    if (actorName == "Cleric Peasant")
    {
        return 525;
    }

    if (actorName == "Regnan Peasant" || actorName == "Pirate")
    {
        return 526;
    }

    if (actorName == "Minotaur Peasant")
    {
        return 527;
    }

    switch (actorGroup)
    {
        case 1:
        case 3:
            return 516;

        case 2:
        case 9:
            return 517;

        case 5:
        case 6:
        case 7:
        case 16:
        case 17:
        case 18:
            return 518;

        case 8:
            return 521;

        case 19:
        case 20:
        case 21:
            return 522;

        case 22:
        case 23:
        case 24:
            return 523;

        case 25:
        case 26:
        case 27:
            return 524;

        case 28:
        case 29:
            return 525;

        case 32:
        case 33:
        case 34:
            return 526;

        case 35:
        case 36:
        case 37:
            return 527;

        default:
            return 0;
    }
}
}

std::optional<GenericActorDialogResolution> resolveGenericActorDialog(
    const std::string &mapFileName,
    const std::string &actorName,
    uint32_t actorGroup,
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable
)
{
    (void)mapFileName;
    (void)actorName;
    uint32_t newsId = 0;
    const std::unordered_map<uint32_t, uint32_t>::const_iterator overrideIt =
        runtimeState.npcGroupNews.find(actorGroup);

    if (overrideIt != runtimeState.npcGroupNews.end())
    {
        newsId = overrideIt->second;
    }
    else
    {
        const std::optional<uint32_t> defaultNewsId = npcDialogTable.getNewsIdForGroup(actorGroup);

        if (defaultNewsId)
        {
            newsId = *defaultNewsId;
        }
    }

    if (newsId == 0 || !npcDialogTable.getNewsText(newsId))
    {
        return std::nullopt;
    }

    GenericActorDialogResolution resolution = {};
    resolution.npcId = resolveGenericNpcId(actorName, actorGroup);
    resolution.newsId = newsId;
    return resolution;
}
}
