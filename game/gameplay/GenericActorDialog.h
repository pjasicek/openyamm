#pragma once

#include "game/events/EventRuntime.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class NpcDialogTable;

struct GenericActorDialogResolution
{
    uint32_t npcId = 0;
    uint32_t newsId = 0;
};

std::optional<GenericActorDialogResolution> resolveGenericActorDialog(
    const std::string &mapFileName,
    const std::string &actorName,
    uint32_t actorGroup,
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable
);
}
