#include "game/GenericActorDialog.h"

#include "game/NpcDialogTable.h"

namespace OpenYAMM::Game
{
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
    resolution.npcId = 0;
    resolution.newsId = newsId;
    return resolution;
}
}
