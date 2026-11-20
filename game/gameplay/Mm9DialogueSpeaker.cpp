#include "game/gameplay/Mm9DialogueSpeaker.h"

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/HouseTable.h"

#include <cmath>
#include <cstdint>

namespace OpenYAMM::Game
{
std::optional<uint32_t> findMm9DialogueSpeakerDecoration(const EventDialogContent &dialog,
    const EventRuntimeState::DialogueRuntimeState &dialogueState)
{
    if (!dialog.isActive || dialog.sourceActorIndex || !dialogueState.mm9RudeSourceDecorationKey)
    {
        return std::nullopt;
    }
    if (dialog.presentation == EventDialogPresentation::Mm9Rude)
    {
        return dialogueState.mm9RudeSourceDecorationKey;
    }
    // A venue the prop's talk opened (its innkeeper's inn): the talk waits to come back.
    if (dialog.isHouseDialog && dialogueState.suspendedMm9RudeDialogue
        && !dialogueState.suspendedMm9RudeDialogue->sourceActorIndex)
    {
        return dialogueState.mm9RudeSourceDecorationKey;
    }
    return std::nullopt;
}

Mm9DialogueSpeaker findMm9DialogueSpeaker(const IGameplayWorldRuntime &world, const EventDialogContent &dialog,
    const HouseEntry *pHouse)
{
    if (!dialog.isActive)
    {
        return {};
    }

    GameplayRuntimeActorState actor;

    if (dialog.sourceActorIndex)
    {
        if (!world.actorRuntimeState(*dialog.sourceActorIndex, actor))
        {
            return {};
        }

        return {.actorIndex = size_t(*dialog.sourceActorIndex)};
    }

    if (const EventRuntimeState *pEventState = world.eventRuntimeState(); pEventState != nullptr)
    {
        if (const std::optional<uint32_t> key = findMm9DialogueSpeakerDecoration(dialog, pEventState->dialogueState))
        {
            return {.decorationKey = key};
        }
    }

    uint32_t rudeId = 0;

    if (dialog.presentation == EventDialogPresentation::Mm9Rude)
    {
        rudeId = dialog.sourceId;
    }
    else if (dialog.isHouseDialog && pHouse != nullptr)
    {
        rudeId = pHouse->sourceVendorId != 0 ? pHouse->sourceVendorId : pHouse->sourceServiceId;
    }

    if (rudeId == 0)
    {
        return {};
    }

    std::optional<size_t> nearest;
    float nearestDistance = 0.0f;

    for (size_t index = 0; index < world.mapActorCount(); ++index)
    {
        if (!world.actorRuntimeState(index, actor) || actor.isDead || actor.mm9RudeId <= 0
            || uint32_t(actor.mm9RudeId) != rudeId)
        {
            continue;
        }

        const float distance = std::hypot(actor.preciseX - world.partyX(), actor.preciseY - world.partyY());

        if (!nearest || distance < nearestDistance)
        {
            nearest = index;
            nearestDistance = distance;
        }
    }

    return {.actorIndex = nearest};
}
}
